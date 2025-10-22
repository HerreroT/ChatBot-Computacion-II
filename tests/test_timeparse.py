from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from app.core.config import Settings
from app.core.timeparse import ParsedBookingMessage, TimeParseError, parse_booking_message


def test_parse_booking_message_success():
    settings = Settings()
    tz = ZoneInfo(settings.timezone)
    current = datetime(2024, 8, 1, 12, 0, tzinfo=tz)

    parsed: ParsedBookingMessage = parse_booking_message(
        "corte 25/08 16:00", settings=settings, now=current
    )

    assert parsed.service_code == "haircut"
    assert parsed.service_label == "corte"
    assert parsed.starts_at.year == 2024
    assert parsed.starts_at.tzinfo == tz


def test_parse_booking_message_rollover_year():
    settings = Settings()
    tz = ZoneInfo(settings.timezone)
    current = datetime(2024, 8, 26, 12, 0, tzinfo=tz)

    parsed = parse_booking_message("corte 25/08 16:00", settings=settings, now=current)

    assert parsed.starts_at.year == 2025


@pytest.mark.parametrize("message", ["", "manicure 01/01 09:00", "corte 25/13 10:00"])
def test_parse_booking_message_invalid(message: str):
    settings = Settings()
    tz = ZoneInfo(settings.timezone)
    current = datetime(2024, 8, 1, 12, 0, tzinfo=tz)

    with pytest.raises(TimeParseError):
        parse_booking_message(message, settings=settings, now=current)
