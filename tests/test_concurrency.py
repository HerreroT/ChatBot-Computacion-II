from __future__ import annotations

import asyncio

import pytest
import sqlalchemy as sa

from app.db.models import Booking


@pytest.mark.anyio
async def test_concurrent_webhooks_do_not_duplicate(async_client, session_factory):
    payloads = [
        {"from": "+549261111111", "text": "corte 25/08 16:00"},
        {"from": "+549261222222", "text": "corte 25/08 16:00"},
    ]

    responses = await asyncio.gather(
        async_client.post("/webhook/whatsapp", json=payloads[0]),
        async_client.post("/webhook/whatsapp", json=payloads[1]),
    )

    statuses = {resp.json()["status"] for resp in responses}
    assert statuses == {"confirmed", "error"}

    async with session_factory() as session:
        result = await session.execute(sa.select(sa.func.count(Booking.id)))
        count = result.scalar_one()

    assert count == 1
