from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from app.core.config import Settings

MESSAGE_REGEX = re.compile(
    r"^\s*(?P<service>[a-zA-ZñÑáéíóúÁÉÍÓÚüÜ ]+)\s+(?P<day>\d{1,2})[/-](?P<month>\d{1,2})\s+(?P<hour>\d{1,2}):(?P<minute>\d{2})\s*$"
)


class TimeParseError(ValueError):
    pass


@dataclass
class ParsedBookingMessage:
    service_code: str
    service_label: str
    starts_at: datetime


def parse_booking_message(
    message: str,
    settings: Settings,
    *,
    now: datetime | None = None,
) -> ParsedBookingMessage:
    if not message or not message.strip():
        raise TimeParseError("El mensaje no puede estar vacío.")

    match = MESSAGE_REGEX.match(message)
    if not match:
        raise TimeParseError(
            "Formato inválido. Usa 'corte 25/08 16:00'."
        )

    service_raw = match.group("service").strip().lower()
    service_code = settings.supported_services.get(service_raw)
    if not service_code:
        raise TimeParseError(f"Servicio desconocido: {service_raw}.")

    try:
        day = int(match.group("day"))
        month = int(match.group("month"))
        hour = int(match.group("hour"))
        minute = int(match.group("minute"))
    except ValueError as exc:
        raise TimeParseError("Fecha u hora inválida.") from exc

    tz = ZoneInfo(settings.timezone)
    reference = now.astimezone(tz) if now else datetime.now(tz)
    year = reference.year

    try:
        scheduled = datetime(year, month, day, hour, minute, tzinfo=tz)
    except ValueError as exc:
        raise TimeParseError(str(exc)) from exc

    if scheduled <= reference:
        try:
            scheduled = datetime(year + 1, month, day, hour, minute, tzinfo=tz)
        except ValueError as exc:
            raise TimeParseError(str(exc)) from exc

    slot_minutes = settings.booking_slot_minutes
    if slot_minutes > 0 and minute % slot_minutes != 0:
        raise TimeParseError(
            f"El horario debe ser en múltiplos de {slot_minutes} minutos."
        )

    return ParsedBookingMessage(
        service_code=service_code,
        service_label=service_raw,
        starts_at=scheduled,
    )
