from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, Tuple

from app.core.config import Settings


_global_lock = asyncio.Lock()
_slot_locks: Dict[str, Tuple[asyncio.Lock, int]] = {}
_semaphore: asyncio.Semaphore | None = None
_current_limit: int | None = None


def init_booking_semaphore(settings: Settings) -> None:
    global _semaphore, _current_limit
    if _semaphore is None or _current_limit != settings.booking_concurrency:
        _semaphore = asyncio.Semaphore(settings.booking_concurrency)
        _current_limit = settings.booking_concurrency


async def _get_slot_lock(slot_key: str) -> asyncio.Lock:
    async with _global_lock:
        entry = _slot_locks.get(slot_key)
        if entry is None:
            lock = asyncio.Lock()
            _slot_locks[slot_key] = (lock, 1)
            return lock
        lock, refcount = entry
        _slot_locks[slot_key] = (lock, refcount + 1)
        return lock


async def _release_slot_lock(slot_key: str) -> None:
    async with _global_lock:
        lock, refcount = _slot_locks.get(slot_key, (None, 0))  # type: ignore[assignment]
        if lock is None:
            return
        refcount -= 1
        if refcount <= 0 and not lock.locked():
            _slot_locks.pop(slot_key, None)
        else:
            _slot_locks[slot_key] = (lock, refcount)


@asynccontextmanager
async def booking_slot_guard(starts_at: datetime):
    if _semaphore is None:
        raise RuntimeError("Booking semaphore not initialised. Call init_booking_semaphore first.")

    slot_key = starts_at.isoformat()
    await _semaphore.acquire()
    lock = await _get_slot_lock(slot_key)
    await lock.acquire()
    try:
        yield
    finally:
        lock.release()
        await _release_slot_lock(slot_key)
        _semaphore.release()
