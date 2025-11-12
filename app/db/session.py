"""Configuración de sesiones de base de datos para el servidor TCP."""
from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker, Session

from app.common.config import settings


def _to_sync_driver(url: str) -> str:
    """
    Adapta la URL de conexión asíncrona (`aiomysql`, `aiosqlite`, etc.) a su
    contraparte síncrona para trabajar con threads.
    """
    if "+aiomysql" in url:
        return url.replace("+aiomysql", "+pymysql")
    if "+aiosqlite" in url:
        return url.replace("+aiosqlite", "")
    return url


SYNC_DB_URL = _to_sync_driver(settings.DB_URL)

# Motor síncrono
engine = create_engine(
    SYNC_DB_URL,
    echo=False,
    pool_pre_ping=True,
    pool_recycle=300,
    future=True,
)

# Factoría de sesiones con almacenamiento por hilo
_session_factory = sessionmaker(
    bind=engine,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
    future=True,
)

SessionLocal = scoped_session(_session_factory)


def get_session() -> Session:
    """
    Obtiene la sesión asociada al hilo actual. Debe cerrarse llamando a
    `SessionLocal.remove()` cuando deje de utilizarse.
    """
    return SessionLocal()


@contextmanager
def session_scope() -> Iterator[Session]:
    """
    Proporciona una sesión por hilo garantizando commit/rollback seguro.

    Ejemplo:

    ```
    with session_scope() as session:
        # ... operaciones ...
    ```
    """
    session = get_session()
    try:
        yield session
        session.commit()
    except:  # noqa: E722 - re-lanza la excepción original
        session.rollback()
        raise
    finally:
        SessionLocal.remove()

