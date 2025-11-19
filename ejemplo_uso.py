#!/usr/bin/env python3
"""
Ejemplo de uso del sistema de reservas desde Python
Ejecutar: python ejemplo_uso.py
"""
import json
import socket
from datetime import datetime, timedelta


class ClienteReservas:
    """Cliente para conectarse al sistema de reservas."""
    
    def __init__(self, host="127.0.0.1", port=8765):
        self.host = host
        self.port = port
        self.socket = None
        self.buffer = b""
    
    def conectar(self):
        """Conecta al servidor."""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host, self.port))
        print(f"✓ Conectado a {self.host}:{self.port}")
    
    def _recibir_linea(self):
        """Recibe una línea JSON del servidor."""
        while b"\n" not in self.buffer:
            chunk = self.socket.recv(4096)
            if not chunk:
                return None
            self.buffer += chunk
        
        linea, self.buffer = self.buffer.split(b"\n", 1)
        return json.loads(linea.decode("utf-8"))
    
    def _enviar(self, mensaje):
        """Envía un mensaje JSON al servidor."""
        data = json.dumps(mensaje) + "\n"
        self.socket.sendall(data.encode("utf-8"))
    
    def suscribirse(self, tenant_id, usuario):
        """Suscribe al usuario en el sistema."""
        # Recibir mensaje de bienvenida
        welcome = self._recibir_linea()
        print(f"Servidor: {welcome.get('message')}")
        
        # Enviar suscripción
        self._enviar({
            "action": "subscribe",
            "tenant_id": tenant_id,
            "user": usuario
        })
        
        respuesta = self._recibir_linea()
        if respuesta.get("event") == "subscribed":
            print(f"✓ Suscrito como: {respuesta.get('user')}")
            return True
        return False
    
    def listar_horarios(self):
        """Lista todos los horarios disponibles."""
        self._enviar({"action": "list"})
        respuesta = self._recibir_linea()
        
        # Limpiar buffer de respuestas duplicadas
        import time
        time.sleep(0.1)
        while True:
            self.socket.settimeout(0.1)
            try:
                chunk = self.socket.recv(4096)
                if chunk:
                    self.buffer += chunk
                    if b"\n" in self.buffer:
                        self.buffer.split(b"\n", 1)[1]
                else:
                    break
            except socket.timeout:
                break
        self.socket.settimeout(None)
        
        if respuesta.get("event") == "slots":
            return respuesta.get("slots", [])
        return []
    
    def hacer_reserva(self, horario):
        """
        Hace una reserva para el horario especificado.
        
        Args:
            horario: String en formato "YYYY-MM-DD HH:MM"
        
        Returns:
            dict con la información de la reserva o None si falla
        """
        self._enviar({
            "action": "book",
            "slot": horario
        })
        
        respuesta = self._recibir_linea()
        
        if respuesta.get("event") == "book.ok":
            return {
                "codigo": respuesta.get("code"),
                "horario": respuesta.get("display"),
                "disponibles": respuesta.get("available"),
                "ocupados": respuesta.get("occupied"),
                "id": respuesta.get("reservation_id")
            }
        else:
            mensaje = respuesta.get('message', 'Error desconocido')
            print(f"✗ Error: {mensaje}")
            print(f"   Respuesta completa: {respuesta}")
            return None
    
    def cerrar(self):
        """Cierra la conexión."""
        if self.socket:
            self.socket.close()
            print("✓ Conexión cerrada")


def ejemplo_basico():
    """Ejemplo básico de uso."""
    print("\n" + "="*60)
    print("  EJEMPLO BÁSICO - Sistema de Reservas")
    print("="*60 + "\n")
    
    # Crear cliente
    cliente = ClienteReservas()
    
    try:
        # Conectar
        cliente.conectar()
        
        # Suscribirse
        cliente.suscribirse("barberia-01", "PythonUser")
        
        # Listar horarios
        print("\n📅 Horarios disponibles:")
        horarios = cliente.listar_horarios()
        
        for i, slot in enumerate(horarios[:5], 1):
            print(f"  {i}. {slot['display']} - Disponibles: {slot['available']}/{slot['capacity']}")
        
        # Hacer una reserva con el primer horario
        if horarios:
            primer_slot = horarios[0]["slot"]
            print(f"\n✅ Reservando: {horarios[0]['display']}")
            
            reserva = cliente.hacer_reserva(primer_slot)
            
            if reserva:
                print("\n" + "="*60)
                print("  ✓ RESERVA CONFIRMADA")
                print("="*60)
                print(f"  Código:      {reserva['codigo']}")
                print(f"  Horario:     {reserva['horario']}")
                print(f"  Disponibles: {reserva['disponibles']}")
                print(f"  ID:          {reserva['id']}")
                print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
    finally:
        cliente.cerrar()


def ejemplo_multiple_reservas():
    """Ejemplo con múltiples reservas (concurrencia)."""
    print("\n" + "="*60)
    print("  EJEMPLO - Múltiples Reservas (Concurrencia)")
    print("="*60 + "\n")
    
    # Horario para todas las reservas
    horario = "2025-11-20 18:00"
    usuarios = ["Cliente1", "Cliente2", "Cliente3", "Cliente4"]
    
    for usuario in usuarios:
        print(f"\n--- {usuario} intenta reservar ---")
        cliente = ClienteReservas()
        
        try:
            cliente.conectar()
            cliente.suscribirse("barberia-01", usuario)
            
            reserva = cliente.hacer_reserva(horario)
            
            if reserva:
                print(f"✓ {usuario}: Reserva OK - Código {reserva['codigo']}")
                print(f"  Cupos restantes: {reserva['disponibles']}")
            else:
                print(f"✗ {usuario}: No pudo reservar (cupo lleno)")
                
        except Exception as e:
            print(f"✗ Error con {usuario}: {e}")
        finally:
            cliente.cerrar()


def ejemplo_interactivo():
    """Ejemplo interactivo donde el usuario elige."""
    print("\n" + "="*60)
    print("  MODO INTERACTIVO - Sistema de Reservas")
    print("="*60 + "\n")
    
    usuario = input("Ingresa tu nombre: ")
    
    cliente = ClienteReservas()
    
    try:
        cliente.conectar()
        cliente.suscribirse("barberia-01", usuario)
        
        # Listar horarios
        print("\n📅 Horarios disponibles:")
        horarios = cliente.listar_horarios()
        
        if not horarios:
            print("No hay horarios disponibles")
            return
        
        for i, slot in enumerate(horarios, 1):
            print(f"  {i}. {slot['display']} - Disponibles: {slot['available']}/{slot['capacity']}")
        
        # Seleccionar horario
        while True:
            try:
                opcion = int(input(f"\nSelecciona un horario (1-{len(horarios)}): "))
                if 1 <= opcion <= len(horarios):
                    break
                print("Opción inválida")
            except ValueError:
                print("Ingresa un número válido")
        
        # Hacer reserva
        slot_elegido = horarios[opcion - 1]
        print(f"\n✅ Reservando: {slot_elegido['display']}")
        
        reserva = cliente.hacer_reserva(slot_elegido["slot"])
        
        if reserva:
            print("\n" + "="*60)
            print("  ✓ RESERVA CONFIRMADA")
            print("="*60)
            print(f"  Usuario:     {usuario}")
            print(f"  Código:      {reserva['codigo']}")
            print(f"  Horario:     {reserva['horario']}")
            print(f"  Disponibles: {reserva['disponibles']}")
            print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
    finally:
        cliente.cerrar()


if __name__ == "__main__":
    import sys
    
    print("\n╔═══════════════════════════════════════════════════════════╗")
    print("║  SISTEMA DE RESERVAS - EJEMPLOS EN PYTHON               ║")
    print("╚═══════════════════════════════════════════════════════════╝")
    
    print("\nOpciones:")
    print("  1. Ejemplo básico (automático)")
    print("  2. Múltiples reservas (demostrar concurrencia)")
    print("  3. Modo interactivo (tú eliges)")
    
    if len(sys.argv) > 1:
        opcion = sys.argv[1]
    else:
        opcion = input("\nElige una opción (1-3): ")
    
    if opcion == "1":
        ejemplo_basico()
    elif opcion == "2":
        ejemplo_multiple_reservas()
    elif opcion == "3":
        ejemplo_interactivo()
    else:
        print("Opción inválida")

