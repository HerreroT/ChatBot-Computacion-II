"""Tests de concurrencia."""
import pytest
import asyncio
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from httpx import AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_slot_full_409():
    """
    Test de cupos llenos.
    Lanza N requests concurrentes al mismo timeslot.
    """
    # Fecha futura
    tz_ar = ZoneInfo("America/Argentina/Buenos_Aires")
    future = datetime.now(tz_ar) + timedelta(days=7)
    date_str = future.strftime("%d/%m")
    time_str = future.strftime("%H:%M")
    
    # Lanzar requests concurrentes (más que CONCURRENCY_PER_SLOT)
    num_requests = 5
    tasks = []
    
    async with AsyncClient(app=app, base_url="http://test", timeout=30.0) as client:
        async def make_request(i):
            return await client.post(
                "/webhook/whatsapp",
                json={
                    "message_id": f"test-concurrency-{i}",
                    "from": f"+549261111{i:04d}",
                    "body": f"corte {date_str} {time_str}",
                    "tenant_id": "barberia-01"
                }
            )
        
        tasks = [make_request(i) for i in range(num_requests)]
        responses = await asyncio.gather(*tasks)
    
    # Contar respuestas exitosas y rechazadas
    success_count = sum(1 for r in responses if r.status_code == 200)
    conflict_count = sum(1 for r in responses if r.status_code == 409)
    error_count = sum(1 for r in responses if r.status_code >= 500)
    
    # Debería haber CONCURRENCY_PER_SLOT (3) exitosas
    # y el resto con 409
    assert success_count == 3, f"Expected 3 successes, got {success_count}"
    assert conflict_count == num_requests - 3 or error_count > 0





