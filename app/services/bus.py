import asyncio

from typing import Optional
from . import __init__ as _  # quiet lint

startup_event = asyncio.Event()
shutdown_event = asyncio.Event()

# Global queue for forwarding
forward_queue: "asyncio.Queue" = asyncio.Queue()

def queue_size() -> int:
    return forward_queue.qsize()
