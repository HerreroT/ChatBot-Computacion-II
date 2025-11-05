"""Servicio de WebSocket para realtime."""
from typing import Dict, Set
import asyncio
import structlog

from fastapi import WebSocket

logger = structlog.get_logger()


class ConnectionManager:
    """Administrador de conexiones WebSocket por tenant."""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self._lock = asyncio.Lock()
    
    async def connect(self, websocket: WebSocket, tenant_id: str):
        """Conecta un WebSocket a un tenant."""
        await websocket.accept()
        
        async with self._lock:
            if tenant_id not in self.active_connections:
                self.active_connections[tenant_id] = set()
            self.active_connections[tenant_id].add(websocket)
        
        logger.info(
            "websocket_connected",
            tenant_id=tenant_id,
            total_connections=len(self.active_connections.get(tenant_id, set()))
        )
    
    async def disconnect(self, websocket: WebSocket, tenant_id: str):
        """Desconecta un WebSocket de un tenant."""
        async with self._lock:
            if tenant_id in self.active_connections:
                self.active_connections[tenant_id].discard(websocket)
                if not self.active_connections[tenant_id]:
                    del self.active_connections[tenant_id]
        
        logger.info(
            "websocket_disconnected",
            tenant_id=tenant_id
        )
    
    async def broadcast_to_tenant(self, tenant_id: str, event: dict):
        """
        Envía un evento a todos los clientes conectados de un tenant.
        
        Args:
            tenant_id: ID del tenant
            event: Evento a enviar (dict JSON serializable)
        """
        disconnected = set()
        
        async with self._lock:
            connections = self.active_connections.get(tenant_id, set()).copy()
        
        for websocket in connections:
            try:
                await websocket.send_json(event)
            except Exception as e:
                logger.warning(
                    "websocket_send_failed",
                    tenant_id=tenant_id,
                    error=str(e)
                )
                disconnected.add(websocket)
        
        # Limpiar conexiones desconectadas
        if disconnected:
            async with self._lock:
                if tenant_id in self.active_connections:
                    self.active_connections[tenant_id] -= disconnected


# Instancia global del manager
connection_manager = ConnectionManager()


def obfuscate_phone(phone: str) -> str:
    """
    Ofusca un número de teléfono.
    
    Args:
        phone: Número de teléfono (ej: "+5492611111111")
    
    Returns:
        Teléfono ofuscado (ej: "+54********1234")
    """
    if len(phone) < 4:
        return "****"
    
    # Mantener los primeros 3 caracteres y los últimos 4
    return phone[:3] + "*" * (len(phone) - 7) + phone[-4:]

