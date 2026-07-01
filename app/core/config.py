from __future__ import annotations

from functools import lru_cache
from typing import Dict

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="APP_", extra="ignore")

    # App
    name: str = "barber-bot"
    env: str = "dev"
    debug: bool = False
    version: str = "0.1.0"
    log_level: str = "INFO"

    # Database
    database_url: str = "mysql+asyncmy://user:password@mysql:3306/barber_bot"
    db_pool_min_size: int = 1
    db_pool_max_size: int = 5
    db_pool_timeout: float = 30.0

    # Booking / domain
    timezone: str = "America/Argentina/Mendoza"
    booking_concurrency: int = 8
    booking_slot_minutes: int = 30
    supported_services: Dict[str, str] = {"corte": "haircut"}

    # Observability
    metrics_enabled: bool = True

    # Auth
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60


@lru_cache #concurrencias de reservas, zona horaria
def get_settings() -> Settings:
    return Settings()
