from __future__ import annotations

import logging
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.sockets import emit_booking_created
from app.core.booking_lock import booking_slot_guard
from app.core.config import get_settings
from app.core.timeparse import ParsedBookingMessage, TimeParseError, parse_booking_message
from app.db.repositories.booking_repo import BookingRepository, SlotAlreadyBookedError
from app.db.repositories.user_repo import CustomerRepository
from app.db.session import get_db


logger = logging.getLogger(__name__)
router = APIRouter(tags=["webhook"])
settings = get_settings()


def _normalize_phone(phone_number: str) -> str:
    return phone_number.strip().replace(" ", "")


class WhatsAppWebhookPayload(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    sender: str = Field(alias="from")
    text: str


class BookingPayload(BaseModel):
    id: int
    user: str
    service: str
    starts_at: datetime


class WhatsAppWebhookResponse(BaseModel):
    status: Literal["confirmed", "error"]
    message: str
    booking: BookingPayload | None = None


@router.post("/webhook/whatsapp", response_model=WhatsAppWebhookResponse)
async def whatsapp_webhook(
    payload: WhatsAppWebhookPayload,
    session: AsyncSession = Depends(get_db),
) -> WhatsAppWebhookResponse:
    customer_repo = CustomerRepository(session)
    booking_repo = BookingRepository(session)

    try:
        parsed: ParsedBookingMessage = parse_booking_message(payload.text, settings=settings)
    except TimeParseError as exc:
        logger.warning("Invalid booking message", extra={"message": payload.text, "error": str(exc)})
        return WhatsAppWebhookResponse(status="error", message=str(exc))

    phone_number = _normalize_phone(payload.sender)
    if not phone_number:
        return WhatsAppWebhookResponse(status="error", message="Número de teléfono inválido.")

    async with booking_slot_guard(parsed.starts_at):
        customer = await customer_repo.get_or_create(phone_number)
        try:
            booking = await booking_repo.create_booking(
                customer=customer,
                service=parsed.service_code,
                starts_at=parsed.starts_at,
                raw_message=payload.text,
            )
            await session.commit()
        except SlotAlreadyBookedError as exc:
            logger.info(
                "Slot already booked",
                extra={"starts_at": parsed.starts_at.isoformat(), "user": phone_number},
            )
            return WhatsAppWebhookResponse(status="error", message=str(exc))
        except Exception:
            await session.rollback()
            raise

    confirmation = (
        f"Reserva confirmada: {parsed.service_label} el {parsed.starts_at.strftime('%d/%m %H:%M')}."
    )

    response_payload = BookingPayload(
        id=booking.id,
        user=customer.phone_number,
        service=booking.service,
        starts_at=booking.starts_at,
    )

    await emit_booking_created(booking, customer)

    return WhatsAppWebhookResponse(
        status="confirmed",
        message=confirmation,
        booking=response_payload,
    )
