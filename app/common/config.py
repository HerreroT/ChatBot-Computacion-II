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
    
    # Servidor TCP
    TCP_HOST: str = "127.0.0.1"
    TCP_PORT: int = 8765
    
    class Config:
        case_sensitive = True


settings = Settings()
