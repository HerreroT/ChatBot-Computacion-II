from __future__ import annotations

import asyncio
import json
import logging
import uuid
from typing import Dict, List

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.logging import request_id_ctx_var
from app.db.models import Booking, Customer


logger = logging.getLogger(__name__)
router = APIRouter()


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: List[WebSocket] = []
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections.append(websocket)
        logger.info("WebSocket connected", extra={"path": websocket.url.path})

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            if websocket in self._connections:
                self._connections.remove(websocket)
        logger.info("WebSocket disconnected", extra={"path": websocket.url.path})

    async def broadcast(self, payload: Dict) -> None:
        async with self._lock:
            connections = list(self._connections)
        for connection in connections:
            try:
                await connection.send_json(payload)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Failed to broadcast WebSocket message", exc_info=exc)


manager = ConnectionManager()


@router.websocket("/ws/admin")
async def admin_websocket(websocket: WebSocket) -> None:
    request_id = str(uuid.uuid4())
    token = request_id_ctx_var.set(request_id)
    await manager.connect(websocket)
    await websocket.send_json({"event": "connected", "request_id": request_id})
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
    finally:
        request_id_ctx_var.reset(token)


async def emit_booking_created(booking: Booking, customer: Customer) -> None:
    payload = {
        "event": "booking.created",
        "data": {
            "id": booking.id,
            "user": customer.phone_number,
            "service": booking.service,
            "starts_at": booking.starts_at.isoformat(),
        },
    }
    await manager.broadcast(payload)
