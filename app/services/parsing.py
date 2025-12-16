"""Servicio de parseo de mensajes de WhatsApp."""
import re
from typing import Optional

from app.schemas.webhook import ParsedMessage
from app.services.timeutil import parse_datetime


def parse_message(body: str) -> Optional[ParsedMessage]:
    """
    Parsea un mensaje de WhatsApp con formato: "servicio dd/mm HH:MM"
    
    Args:
        body: Mensaje a parsear
    
    Returns:
        ParsedMessage si el parseo es exitoso, None en caso contrario
    """
    # Limpiar el mensaje
    body = body.strip()
    
    # Patrón regex: servicio fecha hora
    pattern = r"^(?P<service>\w+)\s+(?P<date>\d{2}\/\d{2})\s+(?P<hour>\d{1,2}:\d{2})$"
    match = re.match(pattern, body)
    
    if not match:
        return None
    
    service = match.group("service").lower()
    date_str = match.group("date")
    time_str = match.group("hour")
    
    # Validar el servicio
    if service not in ["corte"]:  # TODO: expandir servicios
        return None
    
    # Parsear y convertir a UTC
    try:
        start_at = parse_datetime(date_str, time_str)
    except (ValueError, TypeError):
        return None
    
    return ParsedMessage(
        service=service,
        date_str=date_str,
        time_str=time_str,
        start_at=start_at
    )









