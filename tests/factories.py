from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Booking, Customer


async def create_customer(
    session: AsyncSession,
    *,
    phone_number: str,
) -> Customer:
    customer = Customer(phone_number=phone_number)
    session.add(customer)
    await session.flush()
    return customer


async def create_booking(
    session: AsyncSession,
    *,
    customer: Customer,
    starts_at: datetime,
    service: str = "haircut",
    raw_message: Optional[str] = None,
) -> Booking:
    booking = Booking(
        customer_id=customer.id,
        service=service,
        starts_at=starts_at,
        raw_message=raw_message or f"{service} {starts_at.isoformat()}",
    )
    session.add(booking)
    await session.flush()
    return booking
