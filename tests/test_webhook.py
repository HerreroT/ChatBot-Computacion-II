from __future__ import annotations

import pytest
import sqlalchemy as sa

from app.core.config import Settings
from app.core.timeparse import parse_booking_message
from app.db.models import Booking, Customer
from tests.factories import create_booking, create_customer


@pytest.mark.anyio
async def test_webhook_creates_booking(async_client, session_factory):
    payload = {"from": "+549261123456", "text": "corte 25/08 16:00"}

    resp = await async_client.post("/webhook/whatsapp", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert data["status"] == "confirmed"
    assert data["booking"]["service"] == "haircut"
    assert data["booking"]["user"] == payload["from"]

    async with session_factory() as session:
        result = await session.execute(sa.select(Booking))
        bookings = result.scalars().all()

    assert len(bookings) == 1
    assert bookings[0].raw_message == payload["text"]


@pytest.mark.anyio
async def test_webhook_slot_already_booked(async_client, session_factory):
    settings = Settings()
    parsed = parse_booking_message("corte 25/08 16:00", settings=settings)
    starts_at = parsed.starts_at

    async with session_factory() as session:
        customer = await create_customer(session, phone_number="+549261999999")
        await create_booking(
            session,
            customer=customer,
            starts_at=starts_at,
            service=parsed.service_code,
            raw_message="corte 25/08 16:00",
        )
        await session.commit()

    resp = await async_client.post(
        "/webhook/whatsapp",
        json={"from": "+549261123456", "text": "corte 25/08 16:00"},
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "error"
    assert "ya está reservado" in data["message"]

    async with session_factory() as session:
        result = await session.execute(sa.select(Booking))
        bookings = result.scalars().all()

    assert len(bookings) == 1
