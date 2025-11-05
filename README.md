# ChatBot Computación II - Sistema de Reservas por WhatsApp

Sistema de reservas de barbería por WhatsApp con soporte de WebSocket en tiempo real, control de concurrencia, y observabilidad completa.

## 🚀 Características

- **Webhook WhatsApp**: Endpoint POST para recibir mensajes de WhatsApp
- **Parseo Inteligente**: Reconoce mensajes en formato "servicio dd/mm HH:MM"
- **Control de Concurrencia**: Sistema de cupos por timeslot configurable
- **WebSocket Realtime**: Notificaciones en tiempo real de nuevas reservas
- **Idempotencia**: Prevención de duplicados por `message_id`
- **Observabilidad**: Métricas Prometheus, logging estructurado JSON, health checks
- **Timezone AR**: Soporte completo para timezone de Argentina
- **Async/Await**: Stack completamente asíncrono

## 📋 Requisitos

- Docker y Docker Compose
- Python 3.11+ (para desarrollo local)

## 🏃 Inicio Rápido

### 1. Clonar y configurar

```bash
git clone <repo>
cd ChatBot-Computacion-II
cp .env.example .env  # Opcional, variables ya están en docker-compose
```

### 2. Levantar servicios

```bash
docker-compose up --build
```

Esto levantará:
- **MySQL 8** en puerto 3306
- **API FastAPI** en puerto 8000
- Creará la base de datos y aplicará migraciones automáticamente

### 3. Verificar

```bash
# Health check
curl http://localhost:8000/health

# Documentación interactiva
open http://localhost:8000/docs
```

## 📨 Uso del API

### Crear una Reserva

```bash
curl -X POST http://localhost:8000/webhook/whatsapp \
  -H "Content-Type: application/json" \
  -d '{
    "message_id": "wh-123",
    "from": "+5492611111111",
    "body": "corte 25/08 16:00",
    "tenant_id": "barberia-01"
  }'
```

Respuesta exitosa:
```json
{
  "ok": true,
  "confirmation": "Reserva confirmada: corte el 25/08 a las 16:00 (AR). Código: R-XXXX",
  "code": "R-XXXX"
}
```

### WebSocket para Notificaciones en Tiempo Real

Conéctate a `ws://localhost:8000/ws/{tenant_id}`:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/barberia-01');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Evento:', data.event);  // "reservation.created"
  console.log('Datos:', data.data);
};
```

Evento recibido:
```json
{
  "event": "reservation.created",
  "data": {
    "id": "uuid-reserva",
    "phone_obfuscated": "+54********1111",
    "service": "corte",
    "start_at_local": "25/08 16:00",
    "created_at_local": "01/01 10:00",
    "tenant_id": "barberia-01"
  }
}
```

## 🧪 Tests

```bash
# Instalar dependencias de desarrollo
pip install -r requirements.txt pytest pytest-asyncio httpx

# Ejecutar tests
pytest tests/
```

Tests incluidos:
- `test_webhook.py`: Funcionalidad básica del webhook
- `test_concurrency.py`: Tests de concurrencia y capacidad
- `test_ws.py`: Tests de WebSocket

## ⚙️ Configuración

Variables de entorno (ver `.env.example`):

| Variable | Descripción | Default |
|----------|-------------|---------|
| `DB_URL` | URL de conexión MySQL | `mysql+aiomysql://root:password@db:3306/barber` |
| `TZ` | Timezone | `America/Argentina/Buenos_Aires` |
| `CONCURRENCY_PER_SLOT` | Cupos por timeslot | `3` |
| `LOCAL_SEMAPHORE_SIZE` | Tamaño de semáforo local | `100` |
| `LOG_LEVEL` | Nivel de logging | `INFO` |

## 📊 Observabilidad

### Métricas Prometheus

```bash
curl http://localhost:8000/metrics
```

Métricas personalizadas:
- `reservations_created_total{tenant_id,service}`: Total de reservas creadas
- `reservations_rejected_total{tenant_id,reason}`: Total de rechazos

### Health Check

```bash
curl http://localhost:8000/health
# {"status":"ok","db":"up"}
```

### Logs Estructurados

Todos los logs están en formato JSON para fácil integración con sistemas de logging:

```json
{
  "event": "http_request",
  "method": "POST",
  "path": "/webhook/whatsapp",
  "status_code": 200,
  "duration_ms": 45.2,
  "tenant_id": "barberia-01"
}
```

## 🗂️ Estructura del Proyecto

```
ChatBot-Computacion-II/
├── app/
│   ├── api/
│   │   └── routers/        # Endpoints
│   │       ├── webhook.py  # POST /webhook/whatsapp
│   │       ├── health.py   # GET /health
│   │       └── ws.py       # GET /ws/{tenant_id}
│   ├── db/
│   │   ├── models.py       # Modelos SQLAlchemy
│   │   └── session.py      # Configuración de sesión
│   ├── schemas/            # Schemas Pydantic
│   ├── services/           # Lógica de negocio
│   │   ├── parsing.py      # Parseo de mensajes
│   │   ├── timeutil.py     # Utilidades de tiempo
│   │   ├── reservation_service.py  # Servicio de reservas
│   │   └── realtime.py     # WebSocket manager
│   ├── common/             # Configuración
│   └── main.py             # Aplicación FastAPI
├── alembic/                # Migraciones de BD
├── tests/                  # Tests
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## 🔍 Validaciones

El sistema realiza las siguientes validaciones:

1. **Formato**: Mensaje debe seguir "servicio dd/mm HH:MM"
2. **Servicios**: Solo "corte" aceptado por ahora (extensible)
3. **Fecha**: No puede ser en el pasado
4. **Capacidad**: Controla cupos por timeslot (3 por defecto)
5. **Idempotencia**: No duplica reservas con mismo `message_id`

## 🐛 Errores Comunes

### 422 - Formato Inválido
```json
{"detail": "Formato de mensaje inválido. Usa: 'servicio dd/mm HH:MM'"}
```
**Solución**: Verificar formato del mensaje

### 422 - Fecha Pasada
```json
{"detail": "La fecha ya pasó. Por favor elige una fecha futura."}
```
**Solución**: Usar fecha futura

### 409 - No Hay Cupos
```json
{"detail": "No hay cupos para ese horario"}
```
**Solución**: Elegir otro horario o aumentar `CONCURRENCY_PER_SLOT`

## 📝 TODO

- [ ] Soporte para más servicios (afeitado, peinado, etc.)
- [ ] Mapeo dinámico de servicios por tenant
- [ ] Sistema de notificaciones de cancelación
- [ ] Dashboard web con visualización de reservas
- [ ] Integración real con API de WhatsApp Business
- [ ] Rate limiting por IP
- [ ] Autenticación y autorización

## 👨‍💻 Desarrollo

### Migraciones Alembic

```bash
# Crear nueva migración
alembic revision --autogenerate -m "descripción"

# Aplicar migraciones
alembic upgrade head

# Revertir migración
alembic downgrade -1
```

### Ejecutar sin Docker

```bash
# Instalar dependencias
pip install -r requirements.txt

# Configurar .env
export DB_URL="mysql+aiomysql://root:password@localhost:3306/barber"

# Ejecutar migraciones
alembic upgrade head

# Iniciar servidor
uvicorn app.main:app --reload
```

## 📄 Licencia

MIT

## 🤝 Contribuir

1. Fork el repositorio
2. Crea una rama (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -am 'feat: nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request
