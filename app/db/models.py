"""Modelos de base de datos."""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, String, func, Index
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.dialects.mysql import CHAR as MySQLChar


class Base(DeclarativeBase):
    """Base declarativa para todos los modelos."""
    pass


class Tenant(Base):
    """Modelo de tenant (barbería)."""
    __tablename__ = "tenants"
    
    id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
        comment="ID único del tenant"
    )
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Nombre del tenant"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )
    
    def __repr__(self):
        return f"<Tenant(id={self.id}, name={self.name})>"


class Reservation(Base):
    """Modelo de reserva."""
    __tablename__ = "reservations"
    
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="UUID de la reserva"
    )
    tenant_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="ID del tenant"
    )
    message_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="ID del mensaje WhatsApp (para idempotencia)"
    )
    phone: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="Teléfono del cliente"
    )
    service: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Servicio solicitado"
    )
    start_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        index=True,
        comment="Fecha y hora de la reserva (UTC)"
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="CONFIRMED",
        comment="Estado de la reserva"
    )
    source: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="whatsapp",
        comment="Origen de la reserva"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )
    
    # Índice único para idempotencia
    __table_args__ = (
        Index('idx_tenant_message', 'tenant_id', 'message_id', unique=True),
        Index('idx_tenant_slot', 'tenant_id', 'start_at', 'status'),
    )
    
    def __repr__(self):
        return f"<Reservation(id={self.id}, tenant_id={self.tenant_id}, service={self.service}, start_at={self.start_at})>"





