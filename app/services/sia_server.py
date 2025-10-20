import logging
from typing import List

from pysiaalarm.aio import SIAClient, SIAAccount  # type: ignore

from ..core.config import settings
from .bus import forward_queue
from ..schemas.events import ForwardItem

logger = logging.getLogger("sia-server")

def _build_accounts(ids: List[str], keys: List[str]) -> List[SIAAccount]:
    out: List[SIAAccount] = []
    for i, acc in enumerate(ids):
        key = keys[i] if i < len(keys) else ""
        key = key or None
        if key and len(key) not in (16, 24, 32):
            raise ValueError(f"AES key for account {acc!r} must be 16/24/32 chars, got {len(key)}")
        out.append(SIAAccount(account_id=acc, key=key))
        logger.info("Allowing account=%s (encrypted=%s)", acc, bool(key))
    return out


class SIAService:
    def __init__(self) -> None:
        self.client: SIAClient | None = None

    async def start(self) -> None:
        accounts = _build_accounts(settings.SIA_ACCOUNTS, settings.SIA_KEYS)
        self.client = SIAClient(
            host=settings.SIA_HOST,
            port=settings.SIA_PORT,
            accounts=accounts,
            function=self._on_event,
        )
        await self.client.start()
        logger.info("SIA-DC TCP server listening on %s:%s",
                    settings.SIA_HOST or "0.0.0.0", settings.SIA_PORT)

    async def stop(self) -> None:
        if self.client:
            await self.client.stop()

    async def _on_event(self, event) -> None:
        item = ForwardItem(
            account=getattr(event, "account", None),
            message_type=getattr(event, "message_type", None),
            code=getattr(event, "code", None),
            zone=getattr(event, "zone", None),
            partition=getattr(event, "partition", None),
            receiver=getattr(event, "receiver", None),
            timestamp=getattr(event, "timestamp", None),
            raw=getattr(event, "full_message", None),
            extras=getattr(event, "values", {}) or {},
        )
        logger.info("SIA event: %s", item.model_dump())
        await forward_queue.put(item)

sia_service = SIAService()
