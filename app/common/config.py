"""Configuración de la aplicación."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuración de la aplicación."""
    
    # Base de datos
    DB_URL: str = "mysql+aiomysql://root:password@localhost:3306/barber"
    
    # Timezone
    TZ: str = "America/Argentina/Buenos_Aires"
    
    # Concurrencia
    CONCURRENCY_PER_SLOT: int = 3
    LOCAL_SEMAPHORE_SIZE: int = 100
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    class Config:
        case_sensitive = True


settings = Settings()
