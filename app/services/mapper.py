from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, Optional
from zoneinfo import ZoneInfo

from ..core.config import settings
from ..schemas.events import ForwardItem

# Default heartbeat event codes (SIA). Adjust via env if needed.
DEFAULT_HEARTBEAT_CODES = {"RP", "NP", "YK", "HE", "HB"}

def _to_jakarta_timestamp(dt: Optional[datetime]) -> str:
    """
    Convert to 'YYYY-MM-DD HH:MM:SS' in Asia/Jakarta.
    If None, use now().
    """
    tz = ZoneInfo(settings.APP_TIMEZONE)
    when = dt or datetime.now(tz=ZoneInfo("UTC"))
    if when.tzinfo is None:
        when = when.replace(tzinfo=ZoneInfo("UTC"))
    return when.astimezone(tz).strftime("%Y-%m-%d %H:%M:%S")

def _is_heartbeat(code: Optional[str]) -> bool:
    if not code:
        return False
    hb_set = set(settings.HEARTBEAT_CODES or []) or DEFAULT_HEARTBEAT_CODES
    return code.upper() in hb_set

def _extras_to_message(extras: Dict[str, Any]) -> str:
    """
    Flatten extras dict into a single string like:
    key="value" key2="value2"
    Useful for the 'extra_message' field expected by the target API.
    """
    parts = []
    for k, v in (extras or {}).items():
        if v is None:
            continue
        s = str(v).replace('"', '\\"')
        parts.append(f'{k}="{s}"')
    return " ".join(parts)

def map_to_saras_payload(e: ForwardItem) -> Dict[str, Any]:
    """
    Build the exact JSON body expected by the Frappe API:
    {
      "account_code": "...",
      "event": "1120",
      "partition": "02",
      "zone": "002",
      "extra_message": "...",
      "timestamp": "2025-10-20 14:52:50",
      "is_heartbeat": false
    }
    """
    # Choose which field becomes "event":
    # - Often SIA's `code` (e.g., BA) is used directly.
    # - If you maintain a mapping BA->1120, inject it here.
    event_str = e.code or "UNKN"

    # Partition & zone should be strings; left-pad to 2–3 digits if you need strict width.
    partition = (e.partition or "").zfill(2) if e.partition else None
    zone = (e.zone or "").zfill(3) if e.zone else None

    extras_str = _extras_to_message(e.extras)
    # Also append raw frame (optional, but useful)
    if e.raw:
        extras_str = (extras_str + " " if extras_str else "") + f'raw="{e.raw}"'

    return {
        "account_code": e.account or "",
        "event": event_str,
        "partition": partition,
        "zone": zone,
        "extra_message": extras_str,
        "timestamp": _to_jakarta_timestamp(e.timestamp),
        "is_heartbeat": _is_heartbeat(e.code),
    }
