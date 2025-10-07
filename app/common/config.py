from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="APP_", extra="ignore")

    # App
    name: str = "chatbot-api"
    env: str = "dev"
    debug: bool = True
    version: str = "0.1.0"

    # Database
    database_url: str = (
        "mysql+asyncmy://user:password@localhost:3306/chatbot"
    )

    # Auth
    jwt_secret: str = "change-me-in-prod"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60


def get_settings() -> Settings:
    return Settings()


class HealthStatus(BaseModel):
    status: str
    service: str
    version: str
