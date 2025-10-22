from __future__ import annotations

from pydantic import BaseModel

from app.core.config import Settings, get_settings


class HealthStatus(BaseModel):
    status: str
    service: str
    version: str


__all__ = ["Settings", "get_settings", "HealthStatus"]
