"""Utilidades de manejo de tiempo."""
from datetime import datetime
from zoneinfo import ZoneInfo

from app.common.config import settings


def get_ar_timezone() -> ZoneInfo:
    """Obtiene la zona horaria de Argentina."""
    return ZoneInfo(settings.TZ)


def parse_datetime(date_str: str, time_str: str) -> datetime:
    """
    Parsea una fecha y hora a datetime en timezone AR, luego convierte a UTC.
    
    Args:
        date_str: Fecha en formato "dd/mm"
        time_str: Hora en formato "HH:MM"
    
    Returns:
        datetime en UTC
    """
    tz_ar = get_ar_timezone()
    year = datetime.now(tz_ar).year
    
    # Parsear fecha y hora
    dt_str = f"{date_str}/{year} {time_str}"
    dt_ar = datetime.strptime(dt_str, "%d/%m/%Y %H:%M")
    
    # Asignar timezone AR
    dt_ar = dt_ar.replace(tzinfo=tz_ar)
    
    # Convertir a UTC
    dt_utc = dt_ar.astimezone(ZoneInfo("UTC"))
    
    return dt_utc


def format_datetime_ar(dt: datetime) -> str:
    """
    Formatea un datetime (en UTC) a string en zona horaria AR.
    
    Args:
        dt: datetime en UTC
    
    Returns:
        String formateado como "dd/mm HH:MM (AR)"
    """
    tz_ar = get_ar_timezone()
    dt_ar = dt.replace(tzinfo=ZoneInfo("UTC")).astimezone(tz_ar)
    
    return dt_ar.strftime("%d/%m %H:%M")


def is_past_date(dt: datetime) -> bool:
    """
    Verifica si una fecha ya pasó en la zona horaria AR.
    
    Args:
        dt: datetime en UTC
    
    Returns:
        True si la fecha ya pasó
    """
    tz_ar = get_ar_timezone()
    now_ar = datetime.now(tz_ar)
    dt_ar = dt.replace(tzinfo=ZoneInfo("UTC")).astimezone(tz_ar)
    
    return dt_ar < now_ar






