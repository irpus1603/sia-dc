from fastapi import APIRouter
from ..schemas.events import ReplayEvent, ForwardItem
from ..services.bus import forward_queue

router = APIRouter(prefix="/replay", tags=["tools"])

@router.post("")
async def replay(e: ReplayEvent):
    await forward_queue.put(ForwardItem(**e.model_dump()))
    return {"queued": True}
