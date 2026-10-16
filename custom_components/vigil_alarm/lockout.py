"""The lockout after too many wrong codes: one timer per control point.

Every control point that is registered gets its own count and its own lock timer. Everything that is not
a registered control point (a phone, Home Assistant itself, any made-up name) shares one timer, "other".
A visitor guessing at one panel therefore locks that panel, not the rest of the house. Anybody who can
call the check-code action can still lock "other"; that cannot be avoided, because every code check can be
abused as a lock.

The end of a lock is kept as a wall-clock time in storage, so a restart of Home Assistant, or a reload of
Vigil after changing settings, does not lift it. The count of wrong codes is not kept. A stored end that lies
further away than the longest lock is cut back to it, so a wrong clock cannot lock anyone out for hours.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import CODE_FAILURE_WINDOW, CODE_LOCK_SECONDS, CODE_MAX_FAILURES, DOMAIN

STORAGE_VERSION = 1
OTHER = "other"  # the shared timer for everything that is not a registered control point


class CodeLockout:
    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        clock: Callable[[], float],
        registered: Callable[[], set[str]] = lambda: set(),
    ) -> None:
        self.hass = hass
        self._clock = clock
        self._registered = registered
        self._store: Store[dict[str, Any]] = Store(hass, STORAGE_VERSION, f"{DOMAIN}.lockout.{entry.entry_id}")
        self._failures: dict[str, list[float]] = {}
        self._locked_until: dict[str, float] = {}

    # --------------------------------------------------------------- storage
    async def async_load(self) -> None:
        saved = await self._store.async_load() or {}
        now = self._clock()
        for bucket, until in (saved.get("locked_until") or {}).items():
            try:
                until = float(until)
            except (TypeError, ValueError):
                continue
            if until > now:
                self._locked_until[str(bucket)] = min(until, now + CODE_LOCK_SECONDS)

    def _save(self) -> None:
        self.hass.async_create_task(self._store.async_save({"locked_until": dict(self._locked_until)}))

    async def async_flush(self) -> None:
        await self._store.async_save({"locked_until": self._current()})

    async def async_remove(self) -> None:
        await self._store.async_remove()

    def _current(self) -> dict[str, float]:
        now = self._clock()
        return {b: u for b, u in self._locked_until.items() if u > now}

    # ----------------------------------------------------------------- rules
    def bucket_for(self, source: str | None) -> str:
        return source if source and source in self._registered() else OTHER

    def remaining(self, source: str | None) -> float:
        """Seconds left on the lock for this source, 0 when it may try."""
        until = self._locked_until.get(self.bucket_for(source), 0.0)
        return max(0.0, min(until - self._clock(), CODE_LOCK_SECONDS))

    def record_failure(self, source: str | None) -> str | None:
        """Count a wrong code. The name of the timer that now locks, or None."""
        bucket = self.bucket_for(source)
        now = self._clock()
        recent = [t for t in self._failures.get(bucket, []) if now - t < CODE_FAILURE_WINDOW] + [now]
        if len(recent) >= CODE_MAX_FAILURES:
            self._failures[bucket] = []
            self._locked_until[bucket] = now + CODE_LOCK_SECONDS
            self._locked_until = self._current()
            self._save()
            return bucket
        self._failures[bucket] = recent
        return None

    def clear(self, source: str | None = None) -> bool:
        """Lift the lock of one timer (a control point or "other"), or of all when source is None."""
        if source is None:
            had = bool(self._current())
            self._locked_until.clear()
            self._failures.clear()
        else:
            bucket = self.bucket_for(source) if source != OTHER else OTHER
            had = bucket in self._current()
            self._locked_until.pop(bucket, None)
            self._failures.pop(bucket, None)
        if had:
            self._save()
        return had

    def status(self) -> dict[str, float]:
        """Seconds left per timer that is locked."""
        now = self._clock()
        return {b: round(min(u - now, CODE_LOCK_SECONDS), 1) for b, u in self._current().items()}
