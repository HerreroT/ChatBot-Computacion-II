from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Customer


class CustomerRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_phone(self, phone_number: str) -> Customer | None:
        result = await self.session.execute(
            select(Customer).where(Customer.phone_number == phone_number)
        )
        return result.scalar_one_or_none()

    async def get_or_create(self, phone_number: str) -> Customer:
        existing = await self.get_by_phone(phone_number)
        if existing:
            return existing
        customer = Customer(phone_number=phone_number)
        self.session.add(customer)
        try:
            await self.session.flush()
        except IntegrityError:
            await self.session.rollback()
            result = await self.session.execute(
                select(Customer).where(Customer.phone_number == phone_number)
            )
            customer = result.scalar_one()
        return customer
