"""Schemas para reservas."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ReservationBase(BaseModel):
    """Base para reservas."""
    
    tenant_id: str
    message_id: str
    phone: str
    service: str
    start_at: datetime


class ReservationCreate(ReservationBase):
    """Schema para crear una reserva."""
    
    status: str = "CONFIRMED"
    source: str = "whatsapp"


class ReservationOut(ReservationBase):
    """Schema para devolver una reserva."""
    
    id: str
    status: str
    source: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class ReservationCreatedEvent(BaseModel):
    """Evento de reserva creada."""
    
    id: str
    phone_obfuscated: str
    service: str
    start_at_local: str
    created_at_local: str
    tenant_id: str

