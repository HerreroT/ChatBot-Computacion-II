"""Cálculo de disponibilidades por horario."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Iterable, List

from zoneinfo import ZoneInfo

from app.services.timeutil import format_datetime_ar, get_ar_timezone
from app.services.reservation_service import reservation_service

SLOT_FORMAT = "%Y-%m-%d %H:%M"
UTC = ZoneInfo("UTC")


@dataclass
class SlotInfo:
    """Representa la ocupación de un horario."""

    start_at: datetime  # almacenado en UTC (naive)
    occupied: int
    capacity: int

    @property
    def available(self) -> int:
        return max(self.capacity - self.occupied, 0)

    def as_payload(self) -> dict:
        return {
            "slot": self.start_at.strftime(SLOT_FORMAT),
            "display": format_datetime_ar(self.start_at),
            "occupied": self.occupied,
            "capacity": self.capacity,
            "available": self.available,
        }


def _round_next_interval(
    dt: datetime,
    interval_minutes: int,
) -> datetime:
    """Redondea hacia el próximo múltiplo del intervalo."""
    dt = dt.replace(second=0, microsecond=0)
    remainder = dt.minute % interval_minutes
    if remainder:
        dt += timedelta(minutes=interval_minutes - remainder)
    if dt <= datetime.now(dt.tzinfo or get_ar_timezone()):
        dt += timedelta(minutes=interval_minutes)
    return dt


def _candidate_slots(
    limit: int,
    interval_minutes: int,
) -> Iterable[datetime]:
    tz_ar = get_ar_timezone()
    start_ar = _round_next_interval(datetime.now(tz_ar), interval_minutes)

    for _ in range(limit):
        slot_utc = start_ar.astimezone(UTC).replace(tzinfo=None)
        yield slot_utc
        start_ar += timedelta(minutes=interval_minutes)


def list_available_slots(
    session,
    tenant_id: str,
    limit: int = 8,
    interval_minutes: int = 60,
) -> List[SlotInfo]:
    """
    Devuelve los próximos horarios disponibles para un tenant.
    """
    slots: List[SlotInfo] = []

    for candidate in _candidate_slots(limit * 2, interval_minutes):
        occupied, capacity = reservation_service.occupancy_for_slot(
            session,
            tenant_id,
            candidate,
        )
        info = SlotInfo(
            start_at=candidate,
            occupied=occupied,
            capacity=capacity,
        )
        if info.available > 0:
            slots.append(info)
        if len(slots) >= limit:
            break

    return slots


