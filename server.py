"""Servidor TCP de reservas (standalone).

Demo de Computacion II: sockets + concurrencia + SQLite, usando solo la
biblioteca estandar de Python 3.11+. No requiere Docker, FastAPI ni
dependencias externas.

Protocolo (mensajes JSON delimitados por salto de linea "\n"):

  Cliente -> Servidor
    {"cmd": "LIST_SLOTS"}
    {"cmd": "RESERVE", "slot": "2025-08-25 16:00", "user_id": "u1"}

  Servidor -> Cliente
    {"type": "SLOTS", "slots": [{"slot": "...", "taken": false}, ...]}
    {"type": "RESERVED", "slot": "...", "user_id": "..."}
    {"type": "SLOT_TAKEN", "slot": "..."}
    {"type": "ERROR", "detail": "..."}

  Servidor -> Todos (broadcast en tiempo real)
    {"type": "BROADCAST", "event": "booking.created",
     "slot": "...", "user_id": "..."}
"""

from __future__ import annotations

import json
import socket
import sqlite3
import threading
from datetime import datetime, timedelta

HOST = "0.0.0.0"
PORT = 5555
DB_PATH = "reservations.db"

# Conjunto fijo de horarios disponibles para la demo.
SLOTS: list[str] = [
    (datetime(2025, 8, 25, 9, 0) + timedelta(minutes=30 * i)).strftime("%Y-%m-%d %H:%M")
    for i in range(8)
]

# --- Estado compartido entre threads -------------------------------------
_clients_lock = threading.Lock()
_clients: set[socket.socket] = set()

# SQLite crea un lock interno; ademas serializamos las reservas para que el
# mensaje de RESERVED/SLOT_TAKEN sea coherente con lo que se escribe.
_db_lock = threading.Lock()


def init_db() -> None:
    """Crea la tabla e indice unico que evita reservas duplicadas."""
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS reservations (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                slot     TEXT NOT NULL,
                user_id  TEXT NOT NULL,
                name     TEXT NOT NULL,
                created  TEXT NOT NULL
            )
            """
        )
        # El indice UNIQUE es lo que garantiza que un horario no se reserve
        # dos veces, incluso con clientes concurrentes.
        conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS ux_slot ON reservations(slot)"
        )
        conn.commit()
    finally:
        conn.close()


def list_slots() -> list[dict]:
    """Devuelve los horarios con su estado (tomado o libre)."""
    conn = sqlite3.connect(DB_PATH)
    try:
        rows = conn.execute("SELECT slot FROM reservations").fetchall()
    finally:
        conn.close()
    taken = {r[0] for r in rows}
    return [{"slot": s, "taken": s in taken} for s in SLOTS]


def reserve(slot: str, user_id: str, name: str) -> bool:
    """Intenta reservar un horario. Devuelve True si quedo reservado.

    Se apoya en el indice UNIQUE: si dos clientes piden el mismo slot, solo
    uno logra el INSERT y el otro recibe IntegrityError -> SLOT_TAKEN.
    """
    if slot not in SLOTS:
        raise ValueError(f"slot desconocido: {slot}")

    with _db_lock:
        conn = sqlite3.connect(DB_PATH)
        try:
            conn.execute(
                "INSERT INTO reservations (slot, user_id, name, created) "
                "VALUES (?, ?, ?, ?)",
                (slot, user_id, name, datetime.now().isoformat(timespec="seconds")),
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()


def broadcast(payload: dict, exclude: socket.socket | None = None) -> None:
    """Envia un mensaje a todos los clientes conectados (menos `exclude`)."""
    data = (json.dumps(payload) + "\n").encode("utf-8")
    with _clients_lock:
        targets = [c for c in _clients if c is not exclude]
    for client in targets:
        try:
            client.sendall(data)
        except OSError:
            # Cliente caido; se limpia al cerrar su handler.
            pass


def send(conn: socket.socket, payload: dict) -> None:
    conn.sendall((json.dumps(payload) + "\n").encode("utf-8"))


def handle_client(conn: socket.socket, addr) -> None:
    """Atiende a un cliente. Cada uno corre en su propio thread."""
    print(f"[+] Cliente conectado: {addr}")
    with _clients_lock:
        _clients.add(conn)

    buffer = b""
    try:
        while True:
            chunk = conn.recv(4096)
            if not chunk:
                break  # cliente cerro la conexion
            buffer += chunk

            # Procesa mensajes completos (delimitados por "\n").
            while b"\n" in buffer:
                line, buffer = buffer.split(b"\n", 1)
                line = line.strip()
                if not line:
                    continue
                handle_message(conn, addr, line)
    except ConnectionResetError:
        pass  # el servidor NO se cae si un cliente se desconecta abruptamente
    finally:
        with _clients_lock:
            _clients.discard(conn)
        conn.close()
        print(f"[-] Cliente desconectado: {addr}")


def handle_message(conn: socket.socket, addr, line: bytes) -> None:
    try:
        msg = json.loads(line.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        send(conn, {"type": "ERROR", "detail": "JSON invalido"})
        return

    cmd = msg.get("cmd")

    if cmd == "LIST_SLOTS":
        send(conn, {"type": "SLOTS", "slots": list_slots()})

    elif cmd == "RESERVE":
        slot = msg.get("slot")
        user_id = msg.get("user_id", "anon")
        name = (msg.get("name") or user_id).strip() or "anon"
        if not slot:
            send(conn, {"type": "ERROR", "detail": "falta 'slot'"})
            return
        try:
            ok = reserve(slot, user_id, name)
        except ValueError as exc:
            send(conn, {"type": "ERROR", "detail": str(exc)})
            return

        if ok:
            print(f"[✓] RESERVED {slot} por {name} ({user_id} @ {addr})")
            send(
                conn,
                {"type": "RESERVED", "slot": slot, "user_id": user_id, "name": name},
            )
            # Notifica en tiempo real a los demas clientes.
            broadcast(
                {
                    "type": "BROADCAST",
                    "event": "booking.created",
                    "slot": slot,
                    "user_id": user_id,
                    "name": name,
                },
                exclude=conn,
            )
        else:
            print(f"[x] SLOT_TAKEN {slot} (lo pidio {name})")
            send(conn, {"type": "SLOT_TAKEN", "slot": slot})

    else:
        send(conn, {"type": "ERROR", "detail": f"comando desconocido: {cmd!r}"})


def main() -> None:
    init_db()

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen()

    print(f"TCP listo en {HOST}:{PORT}")
    try:
        while True:
            conn, addr = server.accept()
            # Un thread por cliente => varios clientes concurrentes.
            threading.Thread(
                target=handle_client, args=(conn, addr), daemon=True
            ).start()
    except KeyboardInterrupt:
        print("\nCerrando servidor...")
    finally:
        server.close()


if __name__ == "__main__":
    main()
