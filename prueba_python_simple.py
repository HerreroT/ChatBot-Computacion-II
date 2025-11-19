#!/usr/bin/env python3
"""Prueba simple en Python"""
import json
import socket

print("🐍 PRUEBA SIMPLE EN PYTHON\n")

# Conectar
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(("127.0.0.1", 8765))
print("✓ Conectado\n")

buffer = b""

def recibir():
    global buffer
    while b"\n" not in buffer:
        buffer += client.recv(4096)
    linea, buffer = buffer.split(b"\n", 1)
    return json.loads(linea.decode("utf-8"))

def enviar(msg):
    client.sendall((json.dumps(msg) + "\n").encode("utf-8"))

# Welcome
print("1. Bienvenida:", recibir())

# Subscribe
print("\n2. Suscribiendo...")
enviar({"action": "subscribe", "tenant_id": "barberia-01", "user": "PythonTest"})
print("   Respuesta:", recibir())

# List
print("\n3. Listando horarios...")
enviar({"action": "list"})
import time
time.sleep(0.3)

# Leer slots y limpiar buffer
slots_resp = recibir()
slots = slots_resp["slots"]

# Limpiar buffer duplicado
time.sleep(0.1)
client.settimeout(0.1)
try:
    while True:
        chunk = client.recv(4096)
        if not chunk:
            break
        buffer += chunk
except socket.timeout:
    pass
client.settimeout(None)
buffer = b""  # Limpiar completamente

print(f"   Encontrados {len(slots)} horarios")
for i, slot in enumerate(slots[:3], 1):
    print(f"   {i}. {slot['display']} - Disponibles: {slot['available']}")

# Reservar con horario futuro que tiene cupo
horario_elegido = None
for slot in slots:
    if slot['available'] > 0:
        horario_elegido = slot
        break

if horario_elegido:
    print(f"\n4. Reservando: {horario_elegido['display']}")
    enviar({"action": "book", "slot": horario_elegido["slot"]})
    time.sleep(0.5)
    
    reserva = recibir()
    print(f"   Respuesta: {reserva}")
    
    if reserva.get("event") == "book.ok":
        print(f"\n✅ ÉXITO!")
        print(f"   Código: {reserva['code']}")
        print(f"   Horario: {reserva['display']}")
        print(f"   Cupos restantes: {reserva['available']}")
    else:
        print(f"\n❌ Error: {reserva.get('message')}")
else:
    print("\n⚠️  No hay horarios con cupo disponible")

client.close()
print("\n✓ Conexión cerrada")

