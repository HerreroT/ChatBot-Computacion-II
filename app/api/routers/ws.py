"""Router para WebSocket."""
import structlog
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.realtime import connection_manager

logger = structlog.get_logger()
router = APIRouter(tags=["websocket"])


@router.websocket("/ws/{tenant_id}")
async def websocket_endpoint(websocket: WebSocket, tenant_id: str):
    """
    Endpoint WebSocket para notificaciones en tiempo real.
    
    Eventos emitidos:
    - reservation.created: cuando se crea una nueva reserva
    """
    await connection_manager.connect(websocket, tenant_id)
    
    try:
        while True:
            # Mantener conexión viva y escuchar mensajes del cliente
            data = await websocket.receive_text()
            logger.debug(
                "websocket_message_received",
                tenant_id=tenant_id,
                message=data
            )
    except WebSocketDisconnect:
        await connection_manager.disconnect(websocket, tenant_id)
    except Exception as e:
        logger.error(
            "websocket_error",
            tenant_id=tenant_id,
            error=str(e)
        )
        await connection_manager.disconnect(websocket, tenant_id)





