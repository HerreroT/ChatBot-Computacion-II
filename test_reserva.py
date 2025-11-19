#!/usr/bin/env python3
"""Script para probar el sistema de reservas - Demo"""
import json
import socket
import sys

def conectar_y_reservar(usuario="Cliente1", horario=None):
    """Conecta al servidor y realiza una reserva."""
    
    print("\n╔═══════════════════════════════════════════════════════════╗")
    print("║     SISTEMA DE RESERVAS - BARBERÍA COMPUTACIÓN II       ║")
    print("╚═══════════════════════════════════════════════════════════╝\n")
    
    # Conectar al servidor
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(("127.0.0.1", 8765))
    
    buffer = b""
    
    def recibir_linea():
        nonlocal buffer
        while b"\n" not in buffer:
            buffer += client.recv(4096)
        linea, buffer = buffer.split(b"\n", 1)
        return json.loads(linea.decode("utf-8"))
    
    def enviar(mensaje):
        client.sendall((json.dumps(mensaje) + "\n").encode("utf-8"))
    
    # Mensaje de bienvenida
    print("► Conectándose al servidor...")
    welcome = recibir_linea()
    print(f"  {welcome.get('message')}\n")
    
    # Suscribirse
    print(f"► Suscribiéndose como usuario: {usuario}")
    enviar({"action": "subscribe", "tenant_id": "barberia-01", "user": usuario})
    response = recibir_linea()
    print(f"  ✓ Suscrito: {response.get('user')} - Servicio: {response.get('service')}\n")
    
    # Listar horarios
    print("► Obteniendo horarios disponibles...")
    enviar({"action": "list"})
    slots_response = recibir_linea()
    slots = slots_response.get("slots", [])
    
    print("\n╔═════════════════════════════════════════════════════════╗")
    print("║           HORARIOS DISPONIBLES - HOY                  ║")
    print("╚═════════════════════════════════════════════════════════╝")
    
    for slot in slots:
        disponible = "✓" if slot["available"] > 0 else "✗"
        print(f"  {disponible} {slot['display']} - Disponibles: {slot['available']}/{slot['capacity']}")
    
    # Seleccionar horario
    if not horario:
        print("\n¿Qué horario deseas reservar? (formato: 2025-11-19 14:00)")
        horario = input("Horario: ")
    
    # Hacer reserva
    print(f"\n► Realizando reserva para: {horario}")
    enviar({"action": "book", "slot": horario})
    book_response = recibir_linea()
    
    if book_response.get("event") == "book.ok":
        print("\n╔═════════════════════════════════════════════════════════╗")
        print("║              ✓ RESERVA CONFIRMADA                      ║")
        print("╚═════════════════════════════════════════════════════════╝")
        print(f"  Usuario:     {usuario}")
        print(f"  Fecha/Hora:  {book_response['display']}")
        print(f"  Código:      {book_response['code']}")
        print(f"  Cupos:       {book_response['occupied']} ocupado(s), {book_response['available']} disponible(s)\n")
    else:
        print(f"\n✗ Error en la reserva: {book_response.get('message')}\n")
    
    client.close()
    print("► Conexión cerrada\n")

if __name__ == "__main__":
    usuario = sys.argv[1] if len(sys.argv) > 1 else "Cliente1"
    horario = sys.argv[2] if len(sys.argv) > 2 else None
    conectar_y_reservar(usuario, horario)

