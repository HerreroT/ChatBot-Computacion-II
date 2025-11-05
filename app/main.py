"""Aplicación principal FastAPI."""
from contextlib import asynccontextmanager
import structlog

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.common.logconfig import setup_logging
from app.common.config import settings
from app.api.routers import webhook, health, ws
from app.db.models import Base
from app.db.session import engine

# Setup logging
setup_logging(settings.LOG_LEVEL)
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events de la aplicación."""
    # Startup
    logger.info("starting_app", port=settings.API_PORT)
    yield
    # Shutdown
    logger.info("shutting_down_app")


# Crear aplicación
app = FastAPI(
    title="ChatBot Computación II - Reservas WhatsApp",
    description="Sistema de reservas por WhatsApp con soporte WebSocket",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware de logging estructurado
@app.middleware("http")
async def logging_middleware(request, call_next):
    """Middleware para logging estructurado."""
    import time
    
    start_time = time.time()
    response = await call_next(request)
    duration = (time.time() - start_time) * 1000
    
    # Extraer tenant_id si existe
    tenant_id = None
    if hasattr(request, "path_params") and "tenant_id" in request.path_params:
        tenant_id = request.path_params["tenant_id"]
    
    logger.info(
        "http_request",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_ms=round(duration, 2),
        tenant_id=tenant_id
    )
    
    return response

# Registro de routers
app.include_router(webhook.router)
app.include_router(health.router)
app.include_router(ws.router)

# Prometheus metrics
Instrumentator().instrument(app).expose(app)


@app.get("/")
async def root():
    """Endpoint raíz."""
    return {
        "message": "ChatBot Computación II - API de Reservas WhatsApp",
        "docs": "/docs",
        "health": "/health",
        "metrics": "/metrics"
    }

