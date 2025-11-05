"""Schemas para el webhook de WhatsApp."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class WhatsAppWebhookRequest(BaseModel):
    """Request del webhook de WhatsApp."""
    
    message_id: str = Field(..., description="ID único del mensaje")
    from_: str = Field(..., alias="from", description="Número de teléfono")
    body: str = Field(..., description="Cuerpo del mensaje")
    tenant_id: str = Field(..., description="ID del tenant")
    
    class Config:
        populate_by_name = True


class WhatsAppWebhookResponse(BaseModel):
    """Response del webhook de WhatsApp."""
    
    ok: bool = Field(..., description="Indica si la operación fue exitosa")
    confirmation: Optional[str] = Field(None, description="Mensaje de confirmación")
    error: Optional[str] = Field(None, description="Mensaje de error")
    code: Optional[str] = Field(None, description="Código de la reserva")


class ParsedMessage(BaseModel):
    """Mensaje parseado."""
    
    service: str = Field(..., description="Servicio solicitado")
    date_str: str = Field(..., description="Fecha parseada (dd/mm)")
    time_str: str = Field(..., description="Hora parseada (HH:MM)")
    start_at: datetime = Field(..., description="Fecha completa en UTC")





