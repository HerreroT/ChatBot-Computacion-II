"""Servidor TCP multihilo para gestionar reservas."""
from __future__ import annotations

import json
import socket
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional, Tuple

import structlog

from app.common.config import settings
from app.db.session import session_scope
from app.services.availability import SLOT_FORMAT, list_available_slots
from app.services.reservation_service import (
    ReservationResult,
    SlotFullError,
    reservation_service,
)
from app.services.timeutil import format_datetime_ar

logger = structlog.get_logger(__name__)


@dataclass
class ClientInfo:
    conn: socket.socket
    address: Tuple[str, int]
    tenant_id: str
    user: str
    service: str = "corte"
    send_lock: threading.Lock = field(default_factory=threading.Lock, repr=False)


class SocketReservationServer:
    """Servidor de reservas usando sockets TCP y threads."""

    def __init__(self, host: Optional[str] = None, port: Optional[int] = None) -> None:
        self.host = host or settings.TCP_HOST
        self.port = port or settings.TCP_PORT
        self._clients: Dict[socket.socket, ClientInfo] = {}
        self._clients_lock = threading.Lock()
        self._slot_locks: Dict[Tuple[str, str], threading.Lock] = {}
        self._slot_locks_lock = threading.Lock()

    # Public API ---------------------------------------------------------
    def start(self) -> None:
        """Inicia el loop de aceptación."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((self.host, self.port))
            server_socket.listen()
            logger.info("tcp_server.started", host=self.host, port=self.port)

            try:
                while True:
                    conn, addr = server_socket.accept()
                    thread = threading.Thread(
                        target=self._handle_client,
                        args=(conn, addr),
                        daemon=True,
                    )
                    thread.start()
            except KeyboardInterrupt:
                logger.info("tcp_server.stopped_by_keyboard")

    # Internals ----------------------------------------------------------
    def _handle_client(self, conn: socket.socket, addr: Tuple[str, int]) -> None:
        buffer = b""
        client_info: Optional[ClientInfo] = None

        logger.info("client.connected", address=addr)
        self._send_raw(
            conn,
            {
                "event": "welcome",
                "message": "Conéctate con {'action':'subscribe','tenant_id':'barberia-01','user':'juan'}",
            },
        )

        try:
            while True:
                message, buffer = self._receive_line(conn, buffer)
                if message is None:
                    break

                try:
                    payload = json.loads(message)
                except json.JSONDecodeError:
                    self._send_raw(
                        conn,
                        {"event": "error", "message": "JSON inválido"},
                    )
                    continue

                action = payload.get("action")

                if client_info is None:
                    if action != "subscribe":
                        self._send_raw(
                            conn,
                            {"event": "error", "message": "Primero debes suscribirte"},
                        )
                        continue

                    try:
                        client_info = self._register_client(conn, addr, payload)
                    except ValueError as exc:
                        self._send_raw(
                            conn,
                            {"event": "error", "message": str(exc)},
                        )
                        continue

                    self._send_slots(client_info)
                    continue

                if action == "list":
                    self._send_slots(client_info)
                elif action == "book":
                    self._process_booking(client_info, payload)
                else:
                    self._send_client(
                        client_info,
                        {"event": "error", "message": f"Acción no soportada: {action}"},
                    )
        except ConnectionResetError:
            logger.warning("client.connection_reset", address=addr)
        finally:
            if client_info:
                self._unregister_client(client_info.conn)
            try:
                conn.close()
            except OSError:
                pass
            logger.info("client.disconnected", address=addr)

    def _register_client(
        self,
        conn: socket.socket,
        addr: Tuple[str, int],
        payload: dict,
    ) -> ClientInfo:
        tenant_id = payload.get("tenant_id")
        user = payload.get("user") or f"{addr[0]}:{addr[1]}"
        service = payload.get("service", "corte")

        if not tenant_id:
            raise ValueError("tenant_id es obligatorio en subscribe")

        client_info = ClientInfo(
            conn=conn,
            address=addr,
            tenant_id=tenant_id,
            user=user,
            service=service,
        )
        with self._clients_lock:
            self._clients[conn] = client_info

        logger.info(
            "client.subscribed",
            address=addr,
            tenant_id=tenant_id,
            user=user,
        )
        self._send_client(
            client_info,
            {
                "event": "subscribed",
                "tenant_id": tenant_id,
                "user": user,
                "service": service,
            },
        )
        return client_info

    def _unregister_client(self, conn: socket.socket) -> None:
        with self._clients_lock:
            self._clients.pop(conn, None)

    def _send_slots(self, client: ClientInfo) -> None:
        with session_scope() as session:
            slots = list_available_slots(session, client.tenant_id)

        payload = {
            "event": "slots",
            "tenant_id": client.tenant_id,
            "slots": [slot.as_payload() for slot in slots],
        }
        self._send_client(client, payload)

    def _process_booking(self, client: ClientInfo, payload: dict) -> None:
        slot_str = payload.get("slot")
        if not slot_str:
            self._send_client(
                client,
                {"event": "book.error", "message": "Falta el campo 'slot'"},
            )
            return

        try:
            slot_dt = datetime.strptime(slot_str, SLOT_FORMAT)
        except ValueError:
            self._send_client(
                client,
                {"event": "book.error", "message": "Formato de slot inválido"},
            )
            return

        lock = self._acquire_slot_lock(client.tenant_id, slot_str)
        try:
            with session_scope() as session:
                try:
                    result = reservation_service.create_reservation(
                        session=session,
                        tenant_id=client.tenant_id,
                        phone=client.user,
                        service=client.service,
                        start_at=slot_dt,
                        message_id=payload.get("message_id"),
                    )
                except SlotFullError as exc:
                    self._send_client(
                        client,
                        {"event": "book.error", "message": str(exc)},
                    )
                    return

            confirmation = {
                "event": "book.ok",
                "slot": slot_str,
                "display": format_datetime_ar(slot_dt),
                "reservation_id": result.reservation.id,
                "code": f"R-{result.reservation.id[:8].upper()}",
                "available": max(result.capacity - result.occupied_after, 0),
                "occupied": result.occupied_after,
            }
            self._send_client(client, confirmation)

            self._broadcast(
                tenant_id=client.tenant_id,
                payload={
                    "event": "slot.update",
                    "slot": slot_str,
                    "display": format_datetime_ar(slot_dt),
                    "available": max(result.capacity - result.occupied_after, 0),
                    "occupied": result.occupied_after,
                },
                exclude=client.conn,
            )
        finally:
            lock.release()

    # Helpers ------------------------------------------------------------
    def _acquire_slot_lock(self, tenant_id: str, slot_str: str) -> threading.Lock:
        key = (tenant_id, slot_str)
        with self._slot_locks_lock:
            lock = self._slot_locks.get(key)
            if lock is None:
                lock = threading.Lock()
                self._slot_locks[key] = lock
        lock.acquire()
        return lock

    def _receive_line(
        self,
        conn: socket.socket,
        buffer: bytes,
    ) -> Tuple[Optional[str], bytes]:
        while True:
            if b"\n" in buffer:
                line, buffer = buffer.split(b"\n", 1)
                return line.decode("utf-8").strip(), buffer

            chunk = conn.recv(4096)
            if not chunk:
                return None, b""
            buffer += chunk

    def _send_raw(self, conn: socket.socket, payload: dict) -> None:
        message = json.dumps(payload, ensure_ascii=False) + "\n"
        try:
            conn.sendall(message.encode("utf-8"))
        except OSError:
            pass

    def _send_client(self, client: ClientInfo, payload: dict) -> None:
        message = json.dumps(payload, ensure_ascii=False) + "\n"
        try:
            with client.send_lock:
                client.conn.sendall(message.encode("utf-8"))
        except OSError:
            logger.warning(
                "client.send_failed",
                tenant_id=client.tenant_id,
                user=client.user,
            )
            self._unregister_client(client.conn)

    def _broadcast(
        self,
        tenant_id: str,
        payload: dict,
        exclude: Optional[socket.socket] = None,
    ) -> None:
        with self._clients_lock:
            targets = [
                client
                for client in self._clients.values()
                if client.tenant_id == tenant_id and client.conn != exclude
            ]

        for client in targets:
            self._send_client(client, payload)


def main() -> None:
    server = SocketReservationServer()
    server.start()


if __name__ == "__main__":
    main()


