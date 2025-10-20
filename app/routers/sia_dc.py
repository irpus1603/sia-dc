from fastapi import APIRouter
from ..core.config import settings

router = APIRouter(prefix="/sia-dc", tags=["sia-dc"])

@router.get("/status")
async def status():
    return {
        "listening_host": settings.SIA_HOST or "0.0.0.0",
        "listening_port": settings.SIA_PORT,
        "allowed_accounts": settings.SIA_ACCOUNTS,
        "encrypted_accounts": [a for i, a in enumerate(settings.SIA_ACCOUNTS)
                               if i < len(settings.SIA_KEYS) and bool(settings.SIA_KEYS[i])],
    }
