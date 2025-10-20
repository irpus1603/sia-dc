import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .core.config import settings
from .services.forwarder import forward_worker
from .services.sia_server import sia_service
from .services.bus import startup_event, shutdown_event

from .routers import health as health_router
from .routers import replay as replay_router
from .routers import sia_dc as sia_dc_router

logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger("app")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting services…")
    worker_task = asyncio.create_task(forward_worker())
    await sia_service.start()
    startup_event.set()
    yield
    # Shutdown
    logger.info("Stopping services…")
    shutdown_event.set()
    try:
        await sia_service.stop()
        # Drain queue
        from .services.bus import forward_queue
        await forward_queue.join()
        await asyncio.wait_for(worker_task, timeout=3)
    except Exception:
        worker_task.cancel()

app = FastAPI(title="SIA Receiver (modular routers)", version="1.0.0", lifespan=lifespan)

# Mount routers
app.include_router(health_router.router)
app.include_router(replay_router.router)
app.include_router(sia_dc_router.router)
