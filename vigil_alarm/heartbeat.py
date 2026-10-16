"""Heartbeat: Vigil calls a web address at a fixed interval, so a monitoring service can tell when it stops.

The address is generic: any service that expects a regular call and raises the alarm when it stays
away works (Healthchecks.io is the worked example in the manual). Nothing about a service is
built in. The call carries nothing about the alarm: no state, no names, no codes. It is made
whether or not the alarm is armed.

The address itself is a secret (many services put the key in it). It is never written to the log,
the diagnostics, the event log or a Repair, and the status shown in the panel does not contain it.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any
from urllib.parse import urlsplit

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_call_later, async_track_time_interval
from homeassistant.util import dt as dt_util

from .const import CONF_HEARTBEAT_INTERVAL, CONF_HEARTBEAT_URL, DEFAULT_HEARTBEAT_INTERVAL, DOMAIN, HEARTBEAT_URL_MAX

_LOGGER = logging.getLogger(__name__)

SIGNAL_HEARTBEAT = f"{DOMAIN}_heartbeat_{{}}"
FIRST_PING_DELAY = 30  # seconds after start: let Home Assistant settle, but do not wait a full interval
TIMEOUT = 10  # seconds
FAILURES_FOR_REPAIR = 3


def valid_url(value: Any) -> bool:
    """An http or https address with a host. Nothing else is called."""
    if not isinstance(value, str) or not value or len(value) > HEARTBEAT_URL_MAX:
        return False
    try:
        parts = urlsplit(value)
    except ValueError:
        return False
    return parts.scheme in ("http", "https") and bool(parts.hostname)


class Heartbeat:
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self.last_ok: float | None = None
        self.last_failure: float | None = None
        self.reason: str | None = None  # a short word, never the address
        self.failures = 0  # in a row
        self._unsubs: list = []

    # ------------------------------------------------------------ settings
    @property
    def url(self) -> str:
        return str(self.entry.data.get(CONF_HEARTBEAT_URL) or "")

    @property
    def interval(self) -> int:
        return int(self.entry.data.get(CONF_HEARTBEAT_INTERVAL, DEFAULT_HEARTBEAT_INTERVAL))

    @property
    def enabled(self) -> bool:
        return valid_url(self.url)

    # ---------------------------------------------------------- life cycle
    @callback
    def start(self) -> None:
        if not self.enabled:
            return
        self._unsubs.append(async_call_later(self.hass, FIRST_PING_DELAY, self._tick))
        self._unsubs.append(async_track_time_interval(self.hass, self._tick, timedelta(minutes=self.interval)))

    @callback
    def stop(self) -> None:
        for unsub in self._unsubs:
            unsub()
        self._unsubs.clear()

    async def _tick(self, _now: datetime | None = None) -> None:
        await self.ping()

    # ---------------------------------------------------------------- ping
    async def ping(self) -> bool:
        """Call the address once. True when the service answered with success."""
        if not self.enabled:
            return False
        reason: str | None = None
        try:
            async with async_get_clientsession(self.hass).get(
                self.url, timeout=aiohttp.ClientTimeout(total=TIMEOUT)
            ) as response:
                if response.status >= 400:
                    reason = f"http_{response.status}"
        except TimeoutError:
            reason = "timeout"
        except aiohttp.ClientError:
            reason = "connection"  # the error text may hold the address, so it is not kept
        now = dt_util.utcnow().timestamp()
        if reason is None:
            if self.failures:
                _LOGGER.info("Heartbeat is working again")
            self.last_ok, self.failures, self.reason = now, 0, None
        else:
            self.last_failure, self.reason = now, reason
            self.failures += 1
            if self.failures == 1:
                _LOGGER.warning("Heartbeat could not be sent (%s)", reason)
        async_dispatcher_send(self.hass, SIGNAL_HEARTBEAT.format(self.entry.entry_id))
        return reason is None

    # -------------------------------------------------------------- status
    def status(self) -> dict[str, Any]:
        from .eventlog import rfc3339

        iso = lambda ts: rfc3339(ts) if ts else None  # noqa: E731
        return {
            "enabled": self.enabled,
            "interval": self.interval,
            "last_ok": iso(self.last_ok),
            "last_failure": iso(self.last_failure),
            "reason": self.reason,
            "failures": self.failures,
        }

    def issues(self) -> dict[str, tuple[str, dict[str, str]]]:
        """For the repairs: id -> (text key, placeholders). Only after several failures in a row."""
        if self.failures >= FAILURES_FOR_REPAIR and self.reason:
            return {f"{self.entry.entry_id}_heartbeat_failing": ("heartbeat_failing", {"reason": self.reason})}
        return {}
