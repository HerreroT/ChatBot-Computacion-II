from __future__ import annotations

import json
import logging
import logging.config
import uuid
from contextvars import ContextVar
from typing import Any, Dict

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.types import ASGIApp, Receive, Scope, Send

from app.core.config import Settings


request_id_ctx_var: ContextVar[str | None] = ContextVar("request_id", default=None)


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_ctx_var.get() or "-"
        return True


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_record: Dict[str, Any] = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", "-"),
        }

        if record.exc_info:
            log_record["exc_info"] = self.formatException(record.exc_info)

        if record.stack_info:
            log_record["stack_info"] = self.formatStack(record.stack_info)

        for key, value in record.__dict__.items():
            if key.startswith("_") or key in log_record:
                continue
            try:
                json.dumps(value)
                log_record[key] = value
            except (TypeError, ValueError):
                log_record[key] = str(value)

        return json.dumps(log_record, ensure_ascii=False)


def setup_logging(settings: Settings) -> None:
    handlers = {
        "default": {
            "class": "logging.StreamHandler",
            "level": settings.log_level,
            "formatter": "json",
            "filters": ["request_id"],
        }
    }

    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {
            "request_id": {
                "()": RequestIdFilter,
            }
        },
        "formatters": {
            "json": {
                "()": JsonFormatter,
            }
        },
        "handlers": handlers,
        "loggers": {
            "uvicorn": {"handlers": ["default"], "level": settings.log_level, "propagate": False},
            "uvicorn.error": {"handlers": ["default"], "level": settings.log_level, "propagate": False},
            "uvicorn.access": {"handlers": ["default"], "level": settings.log_level, "propagate": False},
            "app": {"handlers": ["default"], "level": settings.log_level, "propagate": False},
        },
        "root": {
            "handlers": ["default"],
            "level": settings.log_level,
        },
    }

    logging.config.dictConfig(logging_config)


class RequestIdMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        token = request_id_ctx_var.set(request_id)
        try:
            response = await call_next(request)
            response.headers["x-request-id"] = request_id
            return response
        finally:
            request_id_ctx_var.reset(token)


class RequestIdWebSocketMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "websocket":
            await self.app(scope, receive, send)
            return

        request_id = scope.get("headers", [])
        header_dict = {k.decode(): v.decode() for k, v in request_id}
        rid = header_dict.get("x-request-id", str(uuid.uuid4()))
        token = request_id_ctx_var.set(rid)
        try:
            await self.app(scope, receive, send)
        finally:
            request_id_ctx_var.reset(token)
