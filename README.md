# ChatBot-Computacion-II

API base con FastAPI + persistencia MySQL (async) + autenticación JWT.

Requisitos: Python 3.11+, MySQL 8+, `virtualenv`.

## Configuración

- Variables en `.env` (opcionales, con defaults razonables):
  - `APP_NAME` (def: `chatbot-api`)
  - `APP_DEBUG` (def: `true`)
  - `APP_VERSION` (def: `0.1.0`)
  - `APP_DATABASE_URL` (def: `mysql+asyncmy://user:password@localhost:3306/chatbot`)
  - `APP_JWT_SECRET` (def: `change-me-in-prod`)
  - `APP_JWT_ALGORITHM` (def: `HS256`)
  - `APP_ACCESS_TOKEN_EXPIRE_MINUTES` (def: `60`)

Instalar dependencias:

```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Base de datos y migraciones

1) Crear la base en MySQL:

```
CREATE DATABASE chatbot CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'user'@'localhost' IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON chatbot.* TO 'user'@'localhost';
FLUSH PRIVILEGES;
```

2) Ajustar `APP_DATABASE_URL` en `.env`, por ejemplo:

```
APP_DATABASE_URL=mysql+asyncmy://user:password@localhost:3306/chatbot
```

3) Aplicar migraciones:

```
alembic upgrade head
```

> Nota: Alembic está configurado en modo async en `alembic/env.py` y usa `APP_DATABASE_URL`.

## Ejecutar la API

```
uvicorn app.api.main:app --reload
```

Rutas:
- `GET /` → status básico
- `GET /healthz` → chequeo de DB
- `POST /chat` → dummy (crea conversación + mensajes y devuelve eco)

## Autenticación

- Utilidades JWT y hashing en `app/api/auth.py` (passlib + jose).
- Dependencia `get_current_user` lista para proteger rutas.

## Tests

Los tests usan SQLite in-memory (async) para aislar la base.

```
pytest -q
```

Incluye:
- `tests/test_api.py`: prueba `/, /healthz, /chat`.
- `tests/test_models.py`: creación de `User` y `Session`.
