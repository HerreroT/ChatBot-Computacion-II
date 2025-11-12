# ChatBot Computación II - Servidor de Reservas TCP

Implementación sencilla de un sistema de reservas para barbería que funciona
exclusivamente sobre sockets TCP. Cada cliente se conecta con un socket,
recibe los horarios libres y, cuando confirma un turno, el resto de los
clientes conectados se actualiza al instante para evitar choques por
concurrencia.

## 🚀 Características

- Servidor TCP puro: toda la interacción sucede mediante JSON delimitado por
  saltos de línea; no hay FastAPI ni HTTP.
- Multiproceso seguro: cada cliente se atiende en su propio hilo y el acceso a
  la base se protege con locks por horario.
- SQLAlchemy thread-safe: las sesiones se generan por hilo y se limpian
  automáticamente al terminar cada operación.
- Disponibilidad dinámica: solo se listan horarios con cupo disponible y se
  recalculan en tiempo real.
- Notificaciones cruzadas: al confirmar un turno se emite `slot.update` para
  los demás clientes del mismo tenant.

## 📋 Requisitos

- Python 3.11 o superior
- Base MySQL accesible usando la URL indicada en `DB_URL`
- (Opcional) Docker y Docker Compose para levantar la base rápidamente

## 🏃 Inicio rápido

```bash
git clone <repo>
cd ChatBot-Computacion-II
python -m venv .venv
.venv\Scripts\activate  # En Windows
pip install -r requirements.txt
alembic upgrade head        # Crea las tablas si aún no existen
python -m app.socket_srv.server
```

El servidor queda escuchando en `127.0.0.1:8765` (configurable).

## 🔌 Protocolo TCP

Los mensajes son JSON terminados en `\n`.

1. Suscripción (obligatoria):
   ```json
   {"action": "subscribe", "tenant_id": "barberia-01", "user": "clienteA"}
   ```
2. Listar horarios libres:
   ```json
   {"action": "list"}
   ```
3. Reservar un turno:
   ```json
   {"action": "book", "slot": "2025-11-12 14:00"}
   ```

### Ejemplo con `nc`

```bash
nc 127.0.0.1 8765
{"action":"subscribe","tenant_id":"barberia-01","user":"clienteA"}
{"action":"list"}
{"action":"book","slot":"2025-11-12 14:00"}
```

Si otro cliente está conectado recibe automáticamente:

```json
{"event":"slot.update","slot":"2025-11-12 14:00","available":2,"occupied":1}
```

## 🧠 Concurrencia y consistencia

- Se crean locks por `(tenant_id, slot)` para serializar reservas sobre el mismo
  horario.
- `session_scope()` garantiza `commit` o `rollback` seguro antes de liberar el
  hilo.
- El servicio de reservas calcula ocupación y capacidad en la misma transacción
  para evitar sobreventa.

## ⚙️ Configuración

| Variable | Descripción | Default |
|----------|-------------|---------|
| `DB_URL` | URL de conexión a MySQL | `mysql+aiomysql://root:password@db:3306/barber` |
| `TZ` | Zona horaria de trabajo | `America/Argentina/Buenos_Aires` |
| `CONCURRENCY_PER_SLOT` | Cupos máximos por horario | `3` |
| `LOG_LEVEL` | Nivel de logging estructurado | `INFO` |
| `TCP_HOST` | Host donde escucha el servidor | `127.0.0.1` |
| `TCP_PORT` | Puerto TCP del servidor | `8765` |

> Si `DB_URL` usa un driver asíncrono (`+aiomysql`) el servidor lo convierte a
> su equivalente síncrono (`+pymysql`) de forma automática.

## 🗂️ Estructura relevante

```
ChatBot-Computacion-II/
├── app/
│   ├── common/                # Configuración global
│   ├── db/
│   │   ├── models.py          # Modelos SQLAlchemy
│   │   └── session.py         # Session factory thread-safe
│   ├── services/
│   │   ├── availability.py    # Cálculo de horarios libres
│   │   └── reservation_service.py
│   └── socket_srv/
│       └── server.py          # Servidor TCP multihilo
├── alembic/
│   └── versions/              # Migraciones
└── README.md
```

## 🛠️ Desarrollo

- Ejecutá `alembic upgrade head` para preparar la base antes de probar.
- Levantá el servidor con `python -m app.socket_srv.server`.
- Los logs estructurados se imprimen en consola usando `structlog`.

## 🤝 Contribuir

1. Hacé fork del repositorio.
2. Creá una rama (`git checkout -b feature/nueva-funcionalidad`).
3. Documentá cómo probaste el cambio.
4. Abrí un Pull Request.

---

Proyecto licenciado bajo MIT.
