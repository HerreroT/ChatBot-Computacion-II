from datetime import datetime

import pytest
import sqlalchemy as sa
from httpx import ASGITransport, AsyncClient

from app.api.main import create_app
from app.db.models import Message, Reservation


@pytest.fixture()
async def client(session_factory):
    async def override_get_db():
        async with session_factory() as session:
            yield session

    app = create_app()
    app.dependency_overrides = {}
    from app.db.session import get_db as real_get_db

    app.dependency_overrides[real_get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


@pytest.mark.anyio(backend="asyncio")
async def test_root(client: AsyncClient):
    resp = await client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"


@pytest.mark.anyio(backend="asyncio")
async def test_healthz(client: AsyncClient):
    resp = await client.get("/healthz")
    assert resp.status_code == 200


@pytest.mark.anyio(backend="asyncio")
async def test_chat_creates_messages(client: AsyncClient, session_factory):
    resp = await client.post("/chat", json={"message": "hola"})
    assert resp.status_code == 200
    data = resp.json()
    assert "reply" in data

    async with session_factory() as session:
        result = await session.execute(sa.select(sa.func.count(Message.id)))
        count = result.scalar_one()

    assert count == 2
    assert data["conversation_id"] > 0
    assert data["session_id"] > 0


@pytest.mark.anyio(backend="asyncio")
async def test_webhook_whatsapp_creates_reservation(client: AsyncClient, session_factory):
    resp = await client.post(
        "/webhook/whatsapp", json={"message": "corte 25/08 16:00"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["service"] == "corte"
    assert data["reservation_id"] > 0
    assert data["confirmation"].startswith("Reserva confirmada")

    scheduled_from_response = datetime.fromisoformat(data["scheduled_at"])

    async with session_factory() as session:
        result = await session.execute(
            sa.select(Reservation).where(Reservation.id == data["reservation_id"])
        )
        reservation = result.scalar_one()

    assert reservation.service == "corte"
    assert reservation.raw_message == "corte 25/08 16:00"
    assert reservation.scheduled_at == scheduled_from_response
