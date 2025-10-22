# Barber Bot Backend

FastAPI backend for automated barber bookings via WhatsApp. Handles async MySQL persistence, JWT auth, WebSocket notifications, observability, and Dockerized deployment.

## Features
- Async FastAPI + SQLAlchemy (asyncmy) with connection pooling
- WhatsApp webhook parsing (`corte 25/08 16:00`) → creates bookings with slot locking
- Per-slot semaphore guard + DB uniqueness to avoid double reservations under load
- Customer auto-provisioning by phone number
- WebSocket (`/ws/admin`) broadcasting `booking.created` events in real time
- Prometheus metrics at `/metrics`, structured JSON logging with `request_id`
- Alembic migrations, pytest + pytest-asyncio test suite
- Docker Compose for app + MySQL + optional Prometheus

## Configuration
The application reads settings from environment variables (prefix `APP_`). Common options:

```
APP_NAME=barber-bot
APP_ENV=dev
APP_DEBUG=true
APP_DATABASE_URL=mysql+asyncmy://user:password@localhost:3306/barber_bot
APP_JWT_SECRET=change-me
APP_BOOKING_CONCURRENCY=8
APP_BOOKING_SLOT_MINUTES=30
APP_TIMEZONE=America/Argentina/Mendoza
```

Create a `.env` file (loaded automatically by pydantic-settings) or export variables.

## Local Development
Install dependencies and run migrations:

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
```

Start the API:

```
uvicorn app.main:app --reload
```

### WhatsApp Webhook
```
curl -X POST http://localhost:8000/webhook/whatsapp \
     -H "Content-Type: application/json" \
     -d '{"from": "+549261123456", "text": "corte 25/08 16:00"}'
```

### WebSocket Feed
Connect an admin dashboard to `ws://localhost:8000/ws/admin` and listen for `booking.created` payloads.

### Metrics & Health
- `GET /healthz` → DB check 
- `GET /metrics` → Prometheus metrics (gzip enabled)

## Docker
Build and launch the full stack (app + MySQL + Prometheus):

```
docker compose up --build
```

The API listens on `http://localhost:8000`, Prometheus on `http://localhost:9090`. MySQL is exposed on `localhost:3306` (user: `app`, password: `app`).

## Tests
Run the async test suite (uses in-memory SQLite + async engine):

```
pytest
```

Includes parsing, webhook success/error, concurrency guard, WebSocket broadcasting, and legacy model tests.
