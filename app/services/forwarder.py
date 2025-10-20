import asyncio
import logging
import httpx

from app.services.bus import forward_queue, shutdown_event
from app.core.config import settings
from app.schemas.events import ForwardItem
from app.services.mapper import map_to_saras_payload

logger = logging.getLogger("forwarder")

async def _forward_with_retries(item: ForwardItem) -> None:
    body = map_to_saras_payload(item)

    headers = {"Content-Type": "application/json", **settings.FORWARD_EXTRA_HEADERS}
    if settings.FORWARD_COOKIE:
        headers["Cookie"] = settings.FORWARD_COOKIE
    if settings.FORWARD_AUTH_HEADER:
        headers["Authorization"] = settings.FORWARD_AUTH_HEADER

    delay = settings.FORWARD_RETRY_BASE_DELAY
    attempt = 0
    async with httpx.AsyncClient(timeout=settings.FORWARD_TIMEOUT) as client:
        while True:
            try:
                resp = await client.post(settings.FORWARD_URL, json=body, headers=headers)
                if 200 <= resp.status_code < 300:
                    logger.info("Forwarded OK → %s (%s)", settings.FORWARD_URL, resp.status_code)
                    return
                logger.warning("Forward failed (%s): %s", resp.status_code, resp.text)
            except Exception as e:
                logger.error("Forward error: %s", e)

            attempt += 1
            if attempt >= settings.FORWARD_MAX_RETRIES:
                logger.error("Dropping event after %d attempts: %s", attempt, body)
                return

            await asyncio.sleep(delay)
            delay *= 2  # backoff


async def forward_worker() -> None:
    logger.info("Forward worker started")
    while not shutdown_event.is_set():
        try:
            item: ForwardItem = await asyncio.wait_for(forward_queue.get(), timeout=1.0)
        except asyncio.TimeoutError:
            continue
        try:
            await _forward_with_retries(item)
        finally:
            forward_queue.task_done()
    logger.info("Forward worker stopped")
