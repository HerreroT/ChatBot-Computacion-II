"""Tests para el webhook de WhatsApp."""
import pytest
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from httpx import AsyncClient

from app.main import app


@pytest.fixture
def future_date():
    """Fecha futura para las reservas."""
    tz_ar = ZoneInfo("America/Argentina/Buenos_Aires")
    now_ar = datetime.now(tz_ar)
    future = now_ar + timedelta(days=7)
    return future.strftime("%d/%m"), future.strftime("%H:%M")


@pytest.mark.asyncio
async def test_webhook_ok(future_date):
    """Test de webhook exitoso."""
    date_str, time_str = future_date
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/webhook/whatsapp",
            json={
                "message_id": "test-123",
                "from": "+5492611111111",
                "body": f"corte {date_str} {time_str}",
                "tenant_id": "barberia-01"
            }
        )
    
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert "confirmation" in data
    assert "code" in data


@pytest.mark.asyncio
async def test_webhook_idempotent(future_date):
    """Test de idempotencia."""
    date_str, time_str = future_date
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Primera llamada
        response1 = await client.post(
            "/webhook/whatsapp",
            json={
                "message_id": "test-idempotent",
                "from": "+5492611111111",
                "body": f"corte {date_str} {time_str}",
                "tenant_id": "barberia-01"
            }
        )
        
        # Segunda llamada con mismo message_id
        response2 = await client.post(
            "/webhook/whatsapp",
            json={
                "message_id": "test-idempotent",
                "from": "+5492611111111",
                "body": f"corte {date_str} {time_str}",
                "tenant_id": "barberia adaptive01"
            }
        )
    
    assert response1.status_code == 200
    assert response2.status_code == 200
    assert response1.json()["code"] == response2.json()["code"]


@pytest.mark.asyncio
async def test_past_date_422():
    """Test de fecha pasada."""
    # Fecha pasada
    past_date = "01/01"
    past_time = "10:00"
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/webhook/whatsapp",
            json={
                "message_id": "test-past",
                "from": "+5492611111111",
                "body": f"corte {past_date} {past_time}",
                "tenant_id": "barberia-01"
            }
        )
    
    assert response.status_code == 422
    data = response.json()
    assert "ya pasó" in data["detail"].lower()


@pytest.mark.asyncio
async def test_invalid_format_422():
    """Test de formato inválido."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/webhook/whatsapp",
            json={
                "message_id": "test-invalid",
                "from": "+5492611111111",
                "body": "mensaje inválido",
                "tenant_id": "barberia-01"
            }
        )
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_service_not_supported_422(future_date):
    """Test de servicio no soportado."""
    date_str, time_str = future_date
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/webhook/whatsapp",
            json={
                "message_id": "test-service",
                "from": "+5492611111111",
                "body": f"limpieza {date_str} {time_str}",
                "tenant_id": "barberia-01"
            }
        )
    
    assert response.status_code == 422





