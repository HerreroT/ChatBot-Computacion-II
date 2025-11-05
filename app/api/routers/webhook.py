"""Router para webhook de WhatsApp."""
import structlog
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.webhook import WhatsAppWebhookRequest, WhatsAppWebhookResponse
from app.services.parsing import parse_message
from app.services.reservation_service import reservation_service
from app.services.timeutil import is_past_date
from app.common.metrics import metrics

logger = structlog.get_logger()
router = APIRouter(prefix="/webhook", tags=["webhook"])


@router.post("/whatsapp", response_model=WhatsAppWebhookResponse)
async def whatsapp_webhook(
    request: WhatsAppWebhookRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint para recibir mensajes de WhatsApp.
    
    Cocktails de aceptación:
    - Parsea mensaje en formato "servicio dd/mm HH:MM"
    - Verifica idempotencia por message_id
    - Controla concurrencia por slot
    - Devuelve confirmación en español
    """
    try:
        # Parsear mensaje
        parsed = parse_message(request.body)
        
        if not parsed:
            logger.warning(
                "parse_failed",
                body=request.body,
                tenant_id=request.tenant_id
            )
            metrics.inc_rejected(request.tenant_id, "parse_error")
            raise HTTPException(
                status_code=422,
                detail="Formato de mensaje inválido. Usa: 'servicio dd/mm HH:MM'"
            )
        
        # Validar servicio
        if parsed.service not in ["corte"]:
            logger.warning(
                "service_not_supported",
                service=parsed.service,
                tenant_id=request.tenant_id
            )
            metrics.inc_rejected(request.tenant_id, "service_not_supported")
            raise HTTPException(
                status_code=422,
                detail=f"Servicio '{parsed.service}' no soportado. Servicios disponibles: corte"
            )
        
        # Validar fecha
        if is_past_date(parsed.start_at):
            logger.warning(
                "past_date",
                start_at=parsed.start_at.isoformat(),
                tenant_id=request.tenant_id
            )
            metrics.inc_rejected(request.tenant_id, "past_date")
            raise HTTPException(
                status_code=422,
                detail="La fecha ya pasó. Por favor elige una fecha futura."
            )
        
        # Crear reserva
        try:
            reservation, is_new = await reservation_service.create_reservation(
                session=db,
                tenant_id=request.tenant_id,
                message_id=request.message_id,
                phone=request.from_,
                service=parsed.service,
                start_at=parsed.start_at
            )
            await db.commit()
        except ValueError as e:
            await db.rollback()
            raise HTTPException(status_code=409, detail=str(e))
        
        # Generar mensaje de confirmación
        from app.services.timeutil import format_datetime_ar
        
        conf_msg = f"Reserva confirmada: {parsed.service} el {parsed.date_str} a las {parsed.time_str} (AR). Código: R-{reservation.id[:8].upper()}"
        
        return WhatsAppWebhookResponse(
            ok=True,
            confirmation=conf_msg,
            code=f"R-{reservation.id[:8].upper()}"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(
            "webhook_error",
            error=str(e),
            tenant_id=request.tenant_id
        )
        metrics.inc_rejected(request.tenant_id, "internal_error")
        raise HTTPException(status_code=500, detail="Error interno del servidor")




