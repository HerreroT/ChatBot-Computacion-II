"""Servicio de reservas."""
from typing import Tuple, Optional
import structlog
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.config import settings
from app.db.models import Reservation
from app.schemas.reservation import ReservationCreatedEvent
from app.services.realtime import connection_manager, obfuscate_phone
from app.services.timeutil import format_datetime_ar
from app.common.metrics import metrics

logger = structlog.get_logger()


class ReservationService:
    """Servicio para manejar reservas."""
    
    @staticmethod
    async def create_reservation(
        session: AsyncSession,
        tenant_id: str,
        message_id: str,
        phone: str,
        service: str,
        start_at
    ) -> Tuple[Optional[Reservation], bool]:
        """
        Crea una reserva con control de concurrencia transaccional.
        
        Args:
            session: Sesión de base de datos
            tenant_id: ID del tenant
            message_id: ID del mensaje (para idempotencia)
            phone: Teléfono del cliente
            service: Servicio solicitado
            start_at: Datetime en UTC
        
        Returns:
            Tupla (reservation, is_new) donde is_new indica si es civuna nueva reserva
        
        Raises:
            ValueError: Si no hay cupos disponibles
        """
        # 1. Verificar idempotencia
        existing = await session.scalar(
            select(Reservation).where(
                Reservation.tenant_id == tenant_id,
                Reservation.message_id == message_id
            )
        )
        
        if existing:
            logger.info(
                "reservation_exists",
                message_id=message_id,
                tenant_id=tenant_id
            )
            return existing, False
        
        # 2. Verificar capacidad (control de concurrencia)
        count_result = await session.execute(
            select(func.count(Reservation.id)).where(
                Reservation.tenant_id == tenant_id,
                Reservation.start_at == start_at,
                Reservation.status == "CONFIRMED"
            )
        )
        count = count_result.scalar() or 0
        capacity = settings.CONCURRENCY_PER_SLOT
        
        if count >= capacity:
            logger.warning(
                "slot_full",
                tenant_id=tenant_id,
                start_at=start_at.isoformat(),
                count=count,
                capacity=capacity
            )
            metrics.inc_rejected(tenant_id, "slot_full")
            raise ValueError("No hay cupos para ese horario")
        
        # 3. Crear reserva
        reservation = Reservation(
            tenant_id=tenant_id,
            message_id=message_id,
            phone=phone,
            service=service,
            start_at=start_at,
            status="CONFIRMED",
            source="whatsapp"
        )
        
        session.add(reservation)
        await session.flush()  # Para obtener el ID y campos generados por la BD
        
        # Obtener todos los campos necesarios ANTES de que termine la función
        # para evitar problemas con lazy loading
        from datetime import datetime, timezone
        reservation_id = str(reservation.id)
        reservation_phone = str(reservation.phone)
        reservation_service_name = str(reservation.service)
        reservation_start_at = reservation.start_at
        # created_at se genera en el servidor, usar datetime actual (la diferencia es mínima)
        reservation_created_at = datetime.now(timezone.utc)
        
        # Emitir eventos y métricas
        metrics.inc_created(tenant_id, service)
        await ReservationService._emit_reservation_created(
            reservation_id=reservation_id,
            phone=reservation_phone,
            service=reservation_service_name,
            start_at=reservation_start_at,
            created_at=reservation_created_at,
            tenant_id=tenant_id
        )
        
        logger.info(
            "reservation_created",
            reservation_id=reservation_id,
            tenant_id=tenant_id,
            service=service
        )
        
        return reservation, True
    
    @staticmethod
    async def _emit_reservation_created(
        reservation_id: str,
        phone: str,
        service: str,
        start_at,
        created_at,
        tenant_id: str
    ):
        """Emite evento de reserva creada por WebSocket."""
        event = ReservationCreatedEvent(
            id=reservation_id,
            phone_obfuscated=obfuscate_phone(phone),
            service=service,
            start_at_local=format_datetime_ar(start_at),
            created_at_local=format_datetime_ar(created_at),
            tenant_id=tenant_id
        )
        
        await connection_manager.broadcast_to_tenant(
            tenant_id,
            {
                "event": "reservation.created",
                "data": event.model_dump()
            }
        )


reservation_service = ReservationService()

