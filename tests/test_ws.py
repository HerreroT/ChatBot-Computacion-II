"""Tests de WebSocket."""
import pytest
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from httpx import AsyncClient
import json

from app.main import app


@pytest.mark.asyncio
async def test_ws_broadcast():
    """Test de broadcast de reserva por WebSocket."""
    # Fecha futura
    tz_ar = ZoneInfo("America/Argentina/Buenos_Aires")
    future = datetime.now(tz_ar) + timedelta(days=7)
    date_str = future.strftime("%d/%m")
    time_str = future.strftime("%H:%M")
    
    key_event_received = False
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Conectar WebSocket
        async with client.websocket_connect("/ws/barberia-01") as websocket:
            # Crear una reserva
            response = await client.post(
                "/webhook/whatsapp",
                json={
                    "message_id": "test-ws-1",
                    "from": "+5492611111111",
                    "body": f"corte {date_str} {time_str}",
                    "tenant_id": "barberia-01"
                }
            )
            
            assert response.status_code == 200
            
            # Esperar evento en WebSocket
            try:
                data = await websocket.receive_json(timeout=2.0)
                if data.get("event") == "reservation.created":
                    assert "data" in data
                    assert "service" in data["data"]
                    assert data["data"]["service"] == "corte"
                    key_event_received = True
            except Exception as e:
                print(f"Error recibiendo evento: {e}")
    
    assert key_event_received, "No se recibió el evento reservation.created"





