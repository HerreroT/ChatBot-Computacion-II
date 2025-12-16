"""Script de prueba rápida de conexión al servidor TCP."""
import socket
import json
import time

print("🔌 Conectando al servidor TCP en localhost:8765...")

try:
    # Conectarse
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)  # Timeout de 5 segundos
    sock.connect(("127.0.0.1", 8765))
    print("✅ Conectado exitosamente!")

    # Recibir bienvenida
    welcome = sock.recv(4096).decode("utf-8")
    print(f"\n📨 Bienvenida del servidor:")
    print(f"   {welcome.strip()}")

    # Suscribirse
    print("\n📝 Suscribiéndose...")
    subscribe = {"action": "subscribe", "tenant_id": "barberia-01", "user": "test_usuario"}
    sock.sendall((json.dumps(subscribe) + "\n").encode("utf-8"))

    # Recibir respuesta de suscripción
    response1 = sock.recv(4096).decode("utf-8")
    print(f"\n✅ Respuesta de suscripción:")
    try:
        sub_data = json.loads(response1.strip())
        print(f"   Evento: {sub_data.get('event')}")
        print(f"   Tenant: {sub_data.get('tenant_id')}")
        print(f"   Usuario: {sub_data.get('user')}")
    except:
        print(f"   {response1[:200]}")

    # Recibir lista de slots (se envía automáticamente)
    response2 = sock.recv(4096).decode("utf-8")
    print(f"\n📋 Lista de slots recibida:")
    try:
        slots_data = json.loads(response2.strip())
        num_slots = len(slots_data.get("slots", []))
        print(f"   Total de slots disponibles: {num_slots}")
        if num_slots > 0:
            print(f"   Primer slot: {slots_data['slots'][0].get('slot')}")
    except:
        print(f"   {response2[:200]}")

    sock.close()
    print("\n✅ TEST COMPLETO: Todo funciona correctamente!")
    
except ConnectionRefusedError:
    print("❌ ERROR: No se pudo conectar al servidor")
    print("   Verifica que el servidor esté corriendo:")
    print("   docker-compose up")
    
except socket.timeout:
    print("❌ ERROR: Timeout esperando respuesta del servidor")
    
except Exception as e:
    print(f"❌ ERROR: {type(e).__name__}: {e}")

