"""Cliente interactivo para el servidor TCP de reservas.

Flujo:
  1. Pide el NOMBRE del cliente por teclado.
  2. Muestra los turnos disponibles en una lista NUMERADA.
  3. Elegis un turno tipeando su numero.
  4. Reserva ese turno (RESERVE) y muestra RESERVED o SLOT_TAKEN.
  5. Queda escuchando notificaciones en tiempo real de otras reservas.

Para la demo de concurrencia basta con abrir dos terminales y correr este
mismo archivo en cada una, cargando nombres distintos y eligiendo el mismo
numero de turno: uno obtendra RESERVED y el otro SLOT_TAKEN.
"""

from __future__ import annotations

import json
import socket

HOST = "127.0.0.1"
PORT = 5555


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


def pedir_nombre() -> str:
    while True:
        nombre = input("Ingresa el nombre del cliente: ").strip()
        if nombre:
            return nombre
        print("  El nombre no puede estar vacio.")


def elegir_turno(slots: list[dict]) -> str | None:
    """Muestra los turnos numerados y devuelve el slot elegido."""
    print("\nTurnos:")
    for i, item in enumerate(slots, start=1):
        estado = "TOMADO" if item["taken"] else "libre"
        print(f"  {i}. {item['slot']}  [{estado}]")

    while True:
        try:
            opcion = input("\nElegi el numero de turno a reservar (0 = salir): ").strip()
        except (EOFError, KeyboardInterrupt):
            return None
        if opcion == "0":
            return None
        if not opcion.isdigit() or not (1 <= int(opcion) <= len(slots)):
            print("  Opcion invalida, proba de nuevo.")
            continue
        elegido = slots[int(opcion) - 1]
        if elegido["taken"]:
            print("  Ese turno ya esta tomado, elegi otro.")
            continue
        return elegido["slot"]


def main() -> None:
    try:
        nombre = pedir_nombre()
    except (EOFError, KeyboardInterrupt):
        print("\nSaliste sin reservar.")
        return
    user_id = nombre.lower().replace(" ", "_")

    with socket.create_connection((HOST, PORT)) as sock:
        buffer = bytearray()
        print(f"\nConectado a {HOST}:{PORT} como '{nombre}'")

        # 1) Pedir la lista de horarios.
        send(sock, {"cmd": "LIST_SLOTS"})
        resp = recv_message(sock, buffer)
        slots = resp.get("slots", [])

        # 2) Elegir turno por numero.
        slot = elegir_turno(slots)
        if slot is None:
            print("Saliste sin reservar.")
            return

        # 3) Reservar.
        print(f"\nReservando {slot} para {nombre} ...")
        send(sock, {"cmd": "RESERVE", "slot": slot, "user_id": user_id, "name": nombre})

        # Puede llegar algun broadcast antes de la respuesta a nuestro RESERVE.
        while True:
            resp = recv_message(sock, buffer)
            if resp.get("type") in {"RESERVED", "SLOT_TAKEN", "ERROR"}:
                break
            if resp.get("type") == "BROADCAST":
                print(f"  🔔 {resp['name']} reservo {resp['slot']}")

        if resp.get("type") == "RESERVED":
            print(f"✅ RESERVED: {resp['slot']} a nombre de {nombre}")
        elif resp.get("type") == "SLOT_TAKEN":
            print(f"⛔ SLOT_TAKEN: {resp['slot']} (alguien se adelanto)")
        else:
            print(f"Error: {resp.get('detail')}")

        # 4) Escuchar notificaciones en tiempo real.
        print("\nEscuchando reservas de otros clientes (Ctrl+C para salir)...")
        try:
            while True:
                msg = recv_message(sock, buffer)
                if msg.get("type") == "BROADCAST":
                    print(f"  🔔 {msg['name']} reservo {msg['slot']}")
        except (ConnectionError, KeyboardInterrupt):
            print("\nChau!")


if __name__ == "__main__":
    main()
