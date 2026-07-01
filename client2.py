"""Cliente de prueba para el servidor TCP de reservas.

Se conecta al servidor, pide la lista de horarios (LIST_SLOTS) y reserva el
primero que este libre (RESERVE). Luego queda escuchando notificaciones en
tiempo real (broadcast) de reservas hechas por otros clientes.

Para la demo de concurrencia:
  - Copia este archivo como client2.py
  - Cambia user_id = "u2"
  - Ejecuta ambos e intenta reservar el mismo horario:
    uno recibira RESERVED y el otro SLOT_TAKEN.
"""

from __future__ import annotations

import json
import socket
import time

HOST = "127.0.0.1"
PORT = 5555

# Cambiar a "u2" en la copia client2.py para la demo de concurrencia.
user_id = "u1"

# Dejar en None para reservar automaticamente el primer slot libre,
# o fijar un horario ("2025-08-25 16:00") para forzar la colision entre
# los dos clientes en la demo de concurrencia.
slot_a_reservar: str | None = None


def send(sock: socket.socket, payload: dict) -> None:
    sock.sendall((json.dumps(payload) + "\n").encode("utf-8"))


def recv_message(sock: socket.socket, buffer: bytearray) -> dict:
    """Lee del socket hasta obtener un mensaje JSON completo."""
    while b"\n" not in buffer:
        chunk = sock.recv(4096)
        if not chunk:
            raise ConnectionError("el servidor cerro la conexion")
        buffer.extend(chunk)
    line, _, rest = bytes(buffer).partition(b"\n")
    buffer.clear()
    buffer.extend(rest)
    return json.loads(line.decode("utf-8"))


def main() -> None:
    with socket.create_connection((HOST, PORT)) as sock:
        buffer = bytearray()
        print(f"[{user_id}] conectado a {HOST}:{PORT}")

        # 1) Pedir la lista de horarios.
        send(sock, {"cmd": "LIST_SLOTS"})
        resp = recv_message(sock, buffer)
        print(f"[{user_id}] horarios disponibles:")
        libres = []
        for item in resp.get("slots", []):
            estado = "TOMADO" if item["taken"] else "libre"
            print(f"    - {item['slot']}  [{estado}]")
            if not item["taken"]:
                libres.append(item["slot"])

        # 2) Elegir un slot y reservarlo.
        slot = slot_a_reservar or (libres[0] if libres else None)
        if slot is None:
            print(f"[{user_id}] no hay horarios libres para reservar.")
            return

        print(f"[{user_id}] reservando {slot} ...")
        send(sock, {"cmd": "RESERVE", "slot": slot, "user_id": user_id})

        # Puede llegar algun broadcast antes de la respuesta a nuestro RESERVE;
        # lo mostramos pero seguimos esperando la confirmacion propia.
        while True:
            resp = recv_message(sock, buffer)
            if resp.get("type") in {"RESERVED", "SLOT_TAKEN", "ERROR"}:
                break
            if resp.get("type") == "BROADCAST":
                print(f"[{user_id}] 🔔 {resp['user_id']} reservo {resp['slot']}")

        if resp.get("type") == "RESERVED":
            print(f"[{user_id}] ✅ RESERVED: {resp['slot']}")
        elif resp.get("type") == "SLOT_TAKEN":
            print(f"[{user_id}] ⛔ SLOT_TAKEN: {resp['slot']} (ya estaba tomado)")
        else:
            print(f"[{user_id}] respuesta: {resp}")

        # 3) Quedar escuchando notificaciones en tiempo real por unos segundos.
        print(f"[{user_id}] escuchando notificaciones (Ctrl+C para salir)...")
        sock.settimeout(10)
        try:
            while True:
                msg = recv_message(sock, buffer)
                if msg.get("type") == "BROADCAST":
                    print(
                        f"[{user_id}] 🔔 {msg['user_id']} reservo {msg['slot']}"
                    )
        except (socket.timeout, ConnectionError):
            pass

        print(f"[{user_id}] fin.")


if __name__ == "__main__":
    main()
