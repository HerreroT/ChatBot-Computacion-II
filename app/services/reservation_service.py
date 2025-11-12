"""Servicio de reservas sincronizado para el servidor TCP."""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Tuple

import structlog
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.common.config import settings
from app.db.models import Reservation

logger = structlog.get_logger(__name__)


class SlotFullError(Exception):
    """Se lanza cuando el cupo de un horario está completo."""


@dataclass
class ReservationResult:
    reservation: Reservation
    is_new: bool
    occupied_after: int
    capacity: int


class ReservationService:
    """Servicio para manejar reservas de manera síncrona."""

    def __init__(self, capacity_per_slot: int) -> None:
        self.capacity_per_slot = capacity_per_slot

    def _count_confirmed(
        self,
        session: Session,
        tenant_id: str,
        start_at: datetime,
    ) -> int:
        """Cuenta reservas confirmadas para un horario."""
        result = session.execute(
            select(func.count(Reservation.id)).where(
                Reservation.tenant_id == tenant_id,
                Reservation.start_at == start_at,
                Reservation.status == "CONFIRMED",
            )
        )
        return int(result.scalar_one() or 0)

    def _find_by_message_id(
        self,
        session: Session,
        tenant_id: str,
        message_id: str,
    ) -> Optional[Reservation]:
        return session.execute(
            select(Reservation).where(
                Reservation.tenant_id == tenant_id,
                Reservation.message_id == message_id,
            )
        ).scalar_one_or_none()

    def create_reservation(
        self,
        session: Session,
        tenant_id: str,
        phone: str,
        service: str,
        start_at: datetime,
        message_id: Optional[str] = None,
    ) -> ReservationResult:
        """
        Crea una reserva garantizando consistencia transaccional.

        Levanta SlotFullError si el horario está lleno.
        """
        message_id = message_id or f"tcp-{uuid.uuid4().hex}"

        existing = self._find_by_message_id(session, tenant_id, message_id)
        if existing:
            occupied = self._count_confirmed(session, tenant_id, existing.start_at)
            logger.info(
                "reservation_exists",
                message_id=message_id,
                tenant_id=tenant_id,
            )
            return ReservationResult(
                reservation=existing,
                is_new=False,
                occupied_after=occupied,
                capacity=self.capacity_per_slot,
            )

        count = self._count_confirmed(session, tenant_id, start_at)
        if count >= self.capacity_per_slot:
            logger.warning(
                "slot_full",
                tenant_id=tenant_id,
                start_at=start_at.isoformat(),
                count=count,
                capacity=self.capacity_per_slot,
            )
            raise SlotFullError("No hay cupos para ese horario")

        reservation = Reservation(
            tenant_id=tenant_id,
            message_id=message_id,
            phone=phone,
            service=service,
            start_at=start_at,
            status="CONFIRMED",
            source="tcp",
        )

        session.add(reservation)
        session.flush()  # obtén ID antes de cerrar la transacción

        occupied_after = count + 1

        logger.info(
            "reservation_created",
            reservation_id=reservation.id,
            tenant_id=tenant_id,
            service=service,
        )

        return ReservationResult(
            reservation=reservation,
            is_new=True,
            occupied_after=occupied_after,
            capacity=self.capacity_per_slot,
        )

    def occupancy_for_slot(
        self,
        session: Session,
        tenant_id: str,
        start_at: datetime,
    ) -> Tuple[int, int]:
        """
        Devuelve una tupla (ocupados, capacidad) para un slot.
        """
        occupied = self._count_confirmed(session, tenant_id, start_at)
        return occupied, self.capacity_per_slot


reservation_service = ReservationService(settings.CONCURRENCY_PER_SLOT)
