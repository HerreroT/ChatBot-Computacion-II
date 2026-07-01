from __future__ import annotations

from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.sockets import router as sockets_router
from app.api.webhook_whatsapp import router as webhook_router
from app.common.config import HealthStatus
from app.core.booking_lock import init_booking_semaphore
from app.core.config import Settings, get_settings
from app.core.logging import RequestIdMiddleware, setup_logging
from app.core.observability import setup_metrics
from app.db.models import Conversation, Message, SenderEnum, Session as ChatSession, User
from app.db.session import get_db


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[int] = None


class ChatResponse(BaseModel):
    reply: str
    conversation_id: int
    session_id: int


DEMO_USER_EMAIL = "demo@example.com"


def create_app() -> FastAPI:
    settings = get_settings()
    _configure_runtime(settings)

    app = FastAPI(title=settings.name, version=settings.version, debug=settings.debug)
    app.add_middleware(RequestIdMiddleware)

    setup_metrics(app, enabled=settings.metrics_enabled)

    @app.get("/", response_model=HealthStatus)
    async def root() -> HealthStatus:
        return HealthStatus(status="ok", service=settings.name, version=settings.version)

    @app.get("/healthz", response_model=HealthStatus)
    async def healthz(session: AsyncSession = Depends(get_db)) -> HealthStatus:
        try:
            await session.execute(text("SELECT 1"))
            return HealthStatus(status="ok", service=settings.name, version=settings.version)
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(exc),
            ) from exc

    @app.post("/chat", response_model=ChatResponse)
    async def chat(
        payload: ChatRequest, session: AsyncSession = Depends(get_db)
    ) -> ChatResponse:
        chat_session_id: Optional[int] = payload.session_id
        if chat_session_id is not None:
            result = await session.execute(
                select(ChatSession).where(ChatSession.id == chat_session_id)
            )
            chat_session = result.scalar_one_or_none()
            if chat_session is None:
                raise HTTPException(status_code=404, detail="Session not found")
        else:
            result = await session.execute(
                select(User).where(User.email == DEMO_USER_EMAIL)
            )
            user = result.scalar_one_or_none()
            if user is None:
                user = User(
                    email=DEMO_USER_EMAIL,
                    hashed_password="not-used-for-demo-chat",
                )
                session.add(user)
                await session.flush()

            chat_session = ChatSession(user_id=user.id)
            session.add(chat_session)
            await session.flush()
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

        reply_text = f"Echo: {payload.message}"
        bot_msg = Message(
            conversation_id=conversation.id,
            sender=SenderEnum.bot,
            content=reply_text,
        )
        session.add(bot_msg)
        await session.commit()

        return ChatResponse(
            reply=reply_text,
            conversation_id=conversation.id,
            session_id=chat_session_id,
        )

    app.include_router(webhook_router)
    app.include_router(sockets_router)

    return app


def _configure_runtime(settings: Settings) -> None:
    setup_logging(settings)
    init_booking_semaphore(settings)


app = create_app()
