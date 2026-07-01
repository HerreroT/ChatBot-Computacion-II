from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Booking, Customer


class SlotAlreadyBookedError(Exception):
    pass


class BookingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_starts_at(self, starts_at: datetime) -> Booking | None:
        result = await self.session.execute(
            select(Booking).where(Booking.starts_at == starts_at)
        )
        return result.scalar_one_or_none()

    async def create_booking(
        self,
        *,
        customer: Customer,
        service: str,
        starts_at: datetime,
        raw_message: str,
    ) -> Booking:
        booking = Booking(
            customer_id=customer.id,
            service=service,
            starts_at=starts_at,
            raw_message=raw_message,
        )
        self.session.add(booking)
        try:
            await self.session.flush()
        except IntegrityError as exc:  #unique
            await self.session.rollback()
            raise SlotAlreadyBookedError("El horario ya está reservado.") from exc
        return booking
