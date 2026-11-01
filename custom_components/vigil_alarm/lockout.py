"""The lockout after too many wrong codes: one count and one lock per control point, in steps.

Every control point that is registered gets its own count and its own lock. Everything that is not a registered
control point (a phone, Home Assistant itself, any made-up name) shares one, "other". A visitor guessing at one
panel therefore locks that panel, not the rest of the house. Anybody who can call the check-code action can still
lock "other"; that cannot be avoided, because every code check can be abused as a lock.

The lock goes in steps (the numbers are settings of Vigil, see `LOCK_DEFAULTS`): the first lock after a few wrong
codes, a longer second one after a few more, a third, and after that a permanent lock that only an administrator
lifts (the *Clear lock* button of the panel). A right code starts all over. Wrong codes that did not lead to a lock
are forgotten too once nobody has tried again for as long as the next lock would last: four wrong codes, an hour away
and one more does not lock a panel that locks after five. "other" has nobody to unlock it, so
there the last step repeats the longest wait instead of locking for good.

The end of a lock, the step and the count are kept in storage, so a restart of Home Assistant, or a reload of
Vigil after changing settings, does not lift anything. A stored end that lies further away than the longest wait
is cut back to it, so a wrong clock cannot lock anyone out for hours.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, NamedTuple

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import DOMAIN, LOCK_DEFAULTS

STORAGE_VERSION = 1
OTHER = "other"  # the shared timer for everything that is not a registered control point


class Locked(NamedTuple):
    """A lock that has just started: which timer, and for how many minutes (None = until an administrator unlocks)."""

    bucket: str
    minutes: int | None


class CodeLockout:
    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        clock: Callable[[], float],
        registered: Callable[[], set[str]] = lambda: set(),
    ) -> None:
        self.hass = hass
        self._entry = entry
        self._clock = clock
        self._registered = registered
        self._store: Store[dict[str, Any]] = Store(hass, STORAGE_VERSION, f"{DOMAIN}.lockout.{entry.entry_id}")
        self._failures: dict[str, int] = {}  # wrong codes in the current step
        self._last_failure: dict[str, float] = {}  # when the last of them was made
        self._step: dict[str, int] = {}  # locks so far (0 to 3)
        self._locked_until: dict[str, float] = {}
        self._permanent: set[str] = set()

    # -------------------------------------------------------------- settings
    def _rules(self) -> dict[str, int]:
        data = getattr(self._entry, "data", None) or {}
        rules = {}
        for key, default in LOCK_DEFAULTS.items():
            try:
                rules[key] = max(1, int(data.get(key, default)))
            except (TypeError, ValueError):
                rules[key] = default
        return rules

    def _longest(self) -> float:
        rules = self._rules()
        return max(rules[f"lock_wait_{n}"] for n in (1, 2, 3)) * 60.0

    # --------------------------------------------------------------- storage
    async def async_load(self) -> None:
        saved = await self._store.async_load() or {}
        now = self._clock()
        longest = self._longest()
        for bucket, until in (saved.get("locked_until") or {}).items():
            try:
                until = float(until)
            except (TypeError, ValueError):
                continue
            if until > now:
                self._locked_until[str(bucket)] = min(until, now + longest)
        self._permanent = {str(b) for b in (saved.get("permanent") or [])}
        for name, target in (("step", self._step), ("failures", self._failures)):
            for bucket, value in (saved.get(name) or {}).items():
                try:
                    target[str(bucket)] = max(0, int(value))
                except (TypeError, ValueError):
                    continue
        for bucket, when in (saved.get("last_failure") or {}).items():
            try:
                self._last_failure[str(bucket)] = float(when)
            except (TypeError, ValueError):
                continue

    def _state(self) -> dict[str, Any]:
        return {
            "locked_until": self._current(),
            "permanent": sorted(self._permanent),
            "step": {b: v for b, v in self._step.items() if v},
            "failures": {b: v for b, v in self._failures.items() if v},
            "last_failure": {b: v for b, v in self._last_failure.items() if self._failures.get(b)},
        }

    def _save(self) -> None:
        self.hass.async_create_task(self._store.async_save(self._state()))

    async def async_flush(self) -> None:
        await self._store.async_save(self._state())

    async def async_remove(self) -> None:
        await self._store.async_remove()

    def _current(self) -> dict[str, float]:
        now = self._clock()
        return {b: u for b, u in self._locked_until.items() if u > now}

    # ----------------------------------------------------------------- rules
    def bucket_for(self, source: str | None) -> str:
        return source if source and source in self._registered() else OTHER

    def remaining(self, source: str | None, bucket: str | None = None) -> float:
        """Seconds left on a timed lock for this source (or a named timer), 0 when it may try."""
        until = self._locked_until.get(bucket or self.bucket_for(source), 0.0)
        return max(0.0, min(until - self._clock(), self._longest()))

    def is_permanent(self, source: str | None, bucket: str | None = None) -> bool:
        return (bucket or self.bucket_for(source)) in self._permanent

    def refusal(self, source: str | None, bucket: str | None = None) -> str | None:
        """Why this source may not try a code now: the key of the error text, or None when it may."""
        if self.is_permanent(source, bucket):
            return "code_locked_permanent"
        if self.remaining(source, bucket):
            return "code_locked"
        return None

    def _forget_old_failures(self, bucket: str) -> None:
        """Wrong codes older than the wait of the next lock no longer count (a lock itself is not touched).
        A stored count without a time (from before this was kept) starts its period now."""
        if not self._failures.get(bucket):
            return
        now = self._clock()
        last = self._last_failure.setdefault(bucket, now)
        step = min(self._step.get(bucket, 0), 3)
        window = self._rules()[f"lock_wait_{min(step + 1, 3)}"] * 60.0
        if now - last > window:
            self._failures.pop(bucket, None)
            self._last_failure.pop(bucket, None)
            self._save()

    def tries(self, bucket: str) -> tuple[int, int]:
        """(wrong codes counted now, how many lead to the next lock) for one timer."""
        self._forget_old_failures(bucket)
        step = min(self._step.get(bucket, 0), 3)
        return self._failures.get(bucket, 0), self._rules()[f"lock_tries_{step + 1}"]

    def phase(self, bucket: str) -> int:
        """How far the locks have gone: 0 none yet, 1 to 3 the locks so far, 4 locked for good."""
        return 4 if bucket in self._permanent else min(self._step.get(bucket, 0), 3)

    def record_failure(self, source: str | None, bucket: str | None = None) -> Locked | None:
        """Count a wrong code. The lock that starts because of it, or None.

        `bucket` names a timer of its own, for the administrator code of a panel."""
        bucket = bucket or self.bucket_for(source)
        rules = self._rules()
        self._forget_old_failures(bucket)
        step = min(self._step.get(bucket, 0), 3)
        count = self._failures.get(bucket, 0) + 1
        if count < rules[f"lock_tries_{step + 1}"]:
            self._failures[bucket] = count
            self._last_failure[bucket] = self._clock()
            self._save()
            return None
        self._failures[bucket] = 0
        self._last_failure.pop(bucket, None)
        now = self._clock()
        if step < 3:
            minutes = rules[f"lock_wait_{step + 1}"]
            self._step[bucket] = step + 1
        elif bucket == OTHER:  # nobody can unlock this one: the longest wait again
            minutes = rules["lock_wait_3"]
        else:
            self._permanent.add(bucket)
            self._locked_until.pop(bucket, None)
            self._save()
            return Locked(bucket, None)
        self._locked_until[bucket] = now + minutes * 60
        self._locked_until = self._current()
        self._save()
        return Locked(bucket, minutes)

    def record_success(self, source: str | None, bucket: str | None = None) -> None:
        """A right code: the count and the step start from zero again."""
        bucket = bucket or self.bucket_for(source)
        self._last_failure.pop(bucket, None)
        if self._failures.pop(bucket, 0) | self._step.pop(bucket, 0):
            self._save()

    def clear(self, bucket: str | None = None) -> bool:
        """Lift the lock of one timer (a control point, its administrator code, or "other"), or of all when None.
        Also forgets the step and the count. True if something was locked."""
        if bucket is None:
            had = bool(self._current()) or bool(self._permanent)
            self._locked_until.clear()
            self._failures.clear()
            self._last_failure.clear()
            self._step.clear()
            self._permanent.clear()
        else:
            had = bucket in self._current() or bucket in self._permanent
            self._locked_until.pop(bucket, None)
            self._failures.pop(bucket, None)
            self._last_failure.pop(bucket, None)
            self._step.pop(bucket, None)
            self._permanent.discard(bucket)
        self._save()
        return had

    def status(self) -> dict[str, float]:
        """Seconds left per timer that is locked for a while."""
        now = self._clock()
        longest = self._longest()
        return {b: round(min(u - now, longest), 1) for b, u in self._current().items()}

    def permanent(self) -> set[str]:
        """The timers that are locked until an administrator unlocks them."""
        return set(self._permanent)
