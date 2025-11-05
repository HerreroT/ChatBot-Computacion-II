"""Router para health check."""
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Health check endpoint.
    
    Returns:
        {"status": "ok", "db": "up" or "down"}
    """
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ok", "db": "up"}
    except Exception:
        return {"status": "ok", "db": "down"}





