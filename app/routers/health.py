from fastapi import APIRouter
from ..services.bus import queue_size
from ..core.config import settings

router = APIRouter(prefix="/health", tags=["health"])

@router.get("")
async def health():
    return {
        "status": "ok",
        "sia_port": settings.SIA_PORT,
        "forward_url": settings.FORWARD_URL,
        "queue_size": queue_size(),
    }
