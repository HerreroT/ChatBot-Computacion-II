from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.config import HealthStatus, get_settings
from app.db.models import (
    Conversation,
    Message,
    Reservation,
    SenderEnum,
    Session as ChatSession,
)
from app.db.session import get_db


MESSAGE_REGEX = re.compile(
    r"^(?P<service>[A-Za-zÁÉÍÓÚáéíóúÑñÜü ]+)\s+(?P<day>\d{1,2})[/-](?P<month>\d{1,2})\s+(?P<hour>\d{1,2}):(?P<minute>\d{2})$",
    flags=re.UNICODE,
)


def _parse_whatsapp_message(message: str) -> tuple[str, datetime]:
    cleaned = message.strip()
    match = MESSAGE_REGEX.match(cleaned)
    if not match:
        raise ValueError(
            "Formato de mensaje inválido. Usa 'servicio dd/mm HH:MM', por ejemplo 'corte 25/08 16:00'."
        )

    service = match.group("service").strip()
    day = int(match.group("day"))
    month = int(match.group("month"))
    hour = int(match.group("hour"))
    minute = int(match.group("minute"))

    now = datetime.now(timezone.utc)
    year = now.year

    try:
        scheduled = datetime(year, month, day, hour, minute, tzinfo=timezone.utc)
    except ValueError as exc:
        raise ValueError(str(exc)) from exc

    if scheduled < now:
        scheduled = datetime(year + 1, month, day, hour, minute, tzinfo=timezone.utc)

    return service, scheduled


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[int] = None


class ChatResponse(BaseModel):
    reply: str
    conversation_id: int
    session_id: int


class WhatsAppWebhookRequest(BaseModel):
    message: str


class WhatsAppWebhookResponse(BaseModel):
    confirmation: str
    service: str
    scheduled_at: datetime
    reservation_id: int


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.name, version=settings.version, debug=settings.debug)

    @app.get("/", response_model=HealthStatus)
    async def root() -> HealthStatus:
        return HealthStatus(status="ok", service=settings.name, version=settings.version)

    @app.get("/healthz", response_model=HealthStatus)
    async def healthz(session: AsyncSession = Depends(get_db)) -> HealthStatus:
        try:
            await session.execute(text("SELECT 1"))
            return HealthStatus(status="ok", service=settings.name, version=settings.version)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))

    @app.post("/chat", response_model=ChatResponse)
    async def chat(
        payload: ChatRequest, session: AsyncSession = Depends(get_db)
    ) -> ChatResponse:
        # Ensure session exists or create one (anonymous/no user linkage for now)
        chat_session_id: Optional[int] = payload.session_id
        if chat_session_id is not None:
            result = await session.execute(
                select(ChatSession).where(ChatSession.id == chat_session_id)
            )
            chat_session = result.scalar_one_or_none()
            if chat_session is None:
                raise HTTPException(status_code=404, detail="Session not found")
        else:
            chat_session = ChatSession(user_id=0)  # 0 = anonymous/guest
            session.add(chat_session)
            await session.flush()  # to populate id
            chat_session_id = chat_session.id

        conversation = Conversation(session_id=chat_session_id)
        session.add(conversation)
        await session.flush()

        user_msg = Message(
            conversation_id=conversation.id,
            sender=SenderEnum.user,
            content=payload.message,
        )
        session.add(user_msg)

        # Dummy bot reply
        reply_text = f"Echo: {payload.message}"
        bot_msg = Message(
            conversation_id=conversation.id,
            sender=SenderEnum.bot,
            content=reply_text,
        )
        session.add(bot_msg)
        await session.commit()

        return ChatResponse(
            reply=reply_text, conversation_id=conversation.id, session_id=chat_session_id
        )

    @app.post("/webhook/whatsapp", response_model=WhatsAppWebhookResponse)
    async def whatsapp_webhook(
        payload: WhatsAppWebhookRequest, session: AsyncSession = Depends(get_db)
    ) -> WhatsAppWebhookResponse:
        try:
            service, scheduled_at = _parse_whatsapp_message(payload.message)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

        reservation = Reservation(
            service=service, scheduled_at=scheduled_at, raw_message=payload.message
        )
        session.add(reservation)
        await session.commit()
        await session.refresh(reservation)

        confirmation = (
            f"Reserva confirmada para {service} el {scheduled_at.strftime('%d/%m/%Y %H:%M')}."
        )

        return WhatsAppWebhookResponse(
            confirmation=confirmation,
            service=reservation.service,
            scheduled_at=reservation.scheduled_at,
            reservation_id=reservation.id,
        )

    return app


app = create_app()
