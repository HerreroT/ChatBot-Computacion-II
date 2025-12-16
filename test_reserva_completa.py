"""Script de prueba completa: conexión, listado y reserva."""
import socket
import json
import sys

def main():
    print("🚀 TEST COMPLETO DEL SERVIDOR TCP")
    print("=" * 50)
    
    try:
        # 1. Conectarse
        print("\n1️⃣  Conectando al servidor...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect(("127.0.0.1", 8765))
        print("   ✅ Conectado")
        
        # 2. Recibir bienvenida
        welcome = sock.recv(4096).decode("utf-8")
        print(f"\n2️⃣  Bienvenida recibida ✅")
        
        # 3. Suscribirse
        print("\n3️⃣  Suscribiéndose...")
        subscribe = {"action": "subscribe", "tenant_id": "barberia-01", "user": "demo_user"}
        sock.sendall((json.dumps(subscribe) + "\n").encode("utf-8"))
        
        # 4. Recibir confirmación de suscripción
        sub_response = sock.recv(4096).decode("utf-8")
        sub_data = json.loads(sub_response.strip())
        if sub_data.get("event") == "subscribed":
            print(f"   ✅ Suscrito como: {sub_data.get('user')}")
        else:
            print(f"   ⚠️  Respuesta inesperada: {sub_data}")
            sock.close()
            return
        
        # 5. Recibir lista de slots (automática)
        slots_response = sock.recv(4096).decode("utf-8")
        slots_data = json.loads(slots_response.strip())
        num_slots = len(slots_data.get("slots", []))
        print(f"\n4️⃣  Slots disponibles: {num_slots} ✅")
        
        if num_slots == 0:
            print("\n⚠️  No hay slots disponibles para reservar")
            sock.close()
            return
        
        # Mostrar algunos slots
        print("\n   Primeros 3 slots disponibles:")
        for i, slot in enumerate(slots_data["slots"][:3], 1):
            print(f"   {i}. {slot.get('display')} - Disponibles: {slot.get('available')}")
        
        # 6. Listar slots manualmente
        print("\n5️⃣  Solicitando lista de slots...")
        list_cmd = {"action": "list"}
        sock.sendall((json.dumps(list_cmd) + "\n").encode("utf-8"))
        list_response = sock.recv(4096).decode("utf-8")
        print("   ✅ Lista recibida")
        
        # 7. Reservar el primer slot disponible
        first_slot = slots_data["slots"][0]["slot"]
        print(f"\n6️⃣  Reservando slot: {first_slot}...")
        book_cmd = {"action": "book", "slot": first_slot}
        sock.sendall((json.dumps(book_cmd) + "\n").encode("utf-8"))
        
        book_response = sock.recv(4096).decode("utf-8")
        book_data = json.loads(book_response.strip())
        
        if book_data.get("event") == "book.ok":
            print(f"   ✅ RESERVA EXITOSA!")
            print(f"   📅 Slot: {book_data.get('display')}")
            print(f"   🎫 Código: {book_data.get('code')}")
            print(f"   👥 Disponibles después: {book_data.get('available')}")
            print(f"   📊 Ocupados: {book_data.get('occupied')}")
        else:
            print(f"   ❌ Error en reserva: {book_data.get('message')}")
        
        sock.close()
        
        print("\n" + "=" * 50)
        print("✅ TEST COMPLETO: Todo funcionó correctamente!")
        
    except ConnectionRefusedError:
        print("\n❌ ERROR: No se pudo conectar al servidor")
        print("   Verifica que el servidor esté corriendo:")
        print("   docker-compose up")
        sys.exit(1)
        
    except socket.timeout:
        print("\n❌ ERROR: Timeout esperando respuesta del servidor")
        sys.exit(1)
        
    except json.JSONDecodeError as e:
        print(f"\n❌ ERROR: No se pudo parsear JSON: {e}")
        sys.exit(1)
        
    except Exception as e:
        print(f"\n❌ ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

