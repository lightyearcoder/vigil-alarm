"""Drives the sirens.

A siren is a set of roles, each filled with an entity: `control` (on/off, a
siren, switch or light entity), optionally `light` (flash), `tone` and
`volume`. Tone and volume are device settings: before the alarm starts they are
set for the cause (if the siren has a profile for it), afterwards the previous
values are put back.

Many sirens (such as the Sonoff SNZB-09P through Zigbee2MQTT) cannot report
whether they are on, so success means "the command was accepted"; `verified` in
the siren_started event says whether the entity actually reports `on`.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any

from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.event import async_call_later

from .items import items_of
from .const import (
    CONF_CAUSES,
    CONF_CONTROL,
    CONF_LIGHT,
    CONF_MAX_DURATION,
    CONF_PARTITIONS,
    CONF_REPEAT_EVERY,
    CONF_TONE,
    CONF_TONE_ENTITY,
    CONF_VOLUME,
    CONF_VOLUME_ENTITY,
    DOMAIN,
    FLAMMABLE_GAS,
    PROFILE_CAUSES,
    SIREN_CAUSES,
    SUBENTRY_SIREN,
)

if TYPE_CHECKING:
    from .manager import VigilManager

_LOGGER = logging.getLogger(__name__)
ENDING = {"disarmed", "trigger_ended"}


@dataclass
class Siren:
    id: str
    name: str
    control: str
    light: str | None
    tone_entity: str | None
    volume_entity: str | None
    max_duration: float
    repeat_every: float
    causes: frozenset[str]
    profiles: dict[str, dict[str, str]]
    partitions: frozenset[str] = frozenset()  # sounds for an intrusion in these partitions; empty: all of them


@dataclass
class _Active:
    saved_tone: str | None = None
    saved_volume: str | None = None
    touched_tone: bool = False
    touched_volume: bool = False
    timers: list[CALLBACK_TYPE] = field(default_factory=list)


class SirenController:
    def __init__(self, hass: HomeAssistant, manager: VigilManager) -> None:
        self.hass = hass
        self.manager = manager
        self.sirens: list[Siren] = []
        # What the last start of each siren came to: "failed" (the command was refused), "sent" (accepted, but the
        # siren does not say it is on) or "confirmed" (the siren says it is on). Not kept over a restart.
        self.last_start: dict[str, dict[str, Any]] = {}
        for sid, sub in items_of(manager.entry).items():
            if sub.subentry_type != SUBENTRY_SIREN:
                continue
            d = sub.data
            self.sirens.append(
                Siren(
                    sid,
                    sub.title,
                    d[CONF_CONTROL],
                    d.get(CONF_LIGHT) or None,
                    d.get(CONF_TONE_ENTITY) or None,
                    d.get(CONF_VOLUME_ENTITY) or None,
                    float(d.get(CONF_MAX_DURATION, 180)),
                    float(d.get(CONF_REPEAT_EVERY, 0)),
                    frozenset(d.get(CONF_CAUSES, SIREN_CAUSES)),
                    {c: dict(d[c]) for c in PROFILE_CAUSES if d.get(c)},
                    frozenset(d.get(CONF_PARTITIONS) or ()),
                )
            )
        self._active: dict[str, _Active] = {}
        self._lock = asyncio.Lock()  # one command sequence at a time, in order

    @property
    def configured(self) -> bool:
        return bool(self.sirens)

    # ---------------------------------------------------------------- input

    @callback
    def handle(self, event: dict[str, Any]) -> None:
        kind = event["type"]
        if kind in ("triggered", "trigger_cause_changed"):
            self._begin(event["cause"], event.get("sensor"), event.get("partition"))
        elif kind in ENDING:
            self._end("alarm_ended", event.get("partition"))

    @callback
    def resume_after_restart(self) -> None:
        for part in self.manager.alarming():
            if part.engine.cause:
                self._begin(part.engine.cause, part.engine.cause_sensor, part.id)

    @staticmethod
    def serves(siren: Siren, cause: str, partition: str | None) -> bool:
        """Does this siren sound for an alarm in this partition? An alarm from a safety sensor (fire, gas, water,
        tamper, 24 hour) is for the whole house: every siren sounds, whatever partitions it was given."""
        return cause != "intrusion" or not siren.partitions or partition in siren.partitions or partition is None

    @callback
    def _begin(self, cause: str, sensor_id: str | None, partition: str | None = None) -> None:
        for siren in self.sirens:
            if not self.serves(siren, cause, partition):
                continue
            # a 24 hour audible alarm sounds the sirens that sound for an intrusion
            if cause in siren.causes or (cause == "alarm24" and "intrusion" in siren.causes):
                self.hass.async_create_task(self._async_start(siren, cause, sensor_id))

    @callback
    def _end(self, reason: str, partition: str | None = None) -> None:
        """Stop the sirens, except those that still have an alarm somewhere else (an intrusion in another
        partition they serve, or an alarm from a safety sensor, which is house wide)."""
        elsewhere = self.manager.alarming(exclude=partition) if partition else []
        # Always queued: a start that is still waiting in the queue must be undone too.
        for siren in self.sirens:
            if any(self.serves(siren, p.engine.cause or "intrusion", p.id) for p in elsewhere):
                continue
            self.hass.async_create_task(self._async_stop(siren, reason))

    @callback
    def silence(self) -> None:
        """Stop all sirens that are sounding, whatever the reason."""
        self._end("silenced")

    @callback
    def async_stop(self) -> None:
        """Cancel the timers. The sirens themselves are left as they are."""
        for active in self._active.values():
            for cancel in active.timers:
                cancel()
            active.timers.clear()

    # ------------------------------------------------------------- commands

    def _gas_is_flammable(self, sensor_id: str | None) -> bool:
        sensor = self.manager.config.sensors.get(sensor_id or "")
        return bool(sensor and sensor.gas_type in FLAMMABLE_GAS)

    async def _call(self, siren: Siren, domain: str, service: str, data: dict[str, Any], what: str) -> bool:
        try:
            await self.hass.services.async_call(domain, service, data, blocking=True)
        except Exception as err:  # noqa: BLE001 - one failing command must not stop the others
            _LOGGER.error("Siren %s: %s failed: %s", siren.name, what, err)
            self.manager.publish("siren_failed", siren=siren.name, action=what, error=str(err))
            return False
        return True

    async def _switch(self, siren: Siren, entity_id: str, on: bool) -> bool:
        domain = entity_id.split(".")[0]
        return await self._call(
            siren, domain, "turn_on" if on else "turn_off", {"entity_id": entity_id},
            "turn_on" if on else "turn_off",
        )

    async def _set_value(self, siren: Siren, entity_id: str, value: str) -> bool:
        domain = entity_id.split(".")[0]
        if domain in ("select", "input_select"):
            return await self._call(siren, domain, "select_option", {"entity_id": entity_id, "option": value}, "set_value")
        if domain in ("number", "input_number"):
            try:
                number = float(value)
            except ValueError:
                self.manager.publish("siren_failed", siren=siren.name, action="set_value", error=f"not a number: {value}")
                return False
            return await self._call(siren, domain, "set_value", {"entity_id": entity_id, "value": number}, "set_value")
        return False

    def _read(self, entity_id: str | None) -> str | None:
        state = self.hass.states.get(entity_id) if entity_id else None
        return None if state is None or state.state in ("unknown", "unavailable") else state.state

    async def _async_start(self, siren: Siren, cause: str, sensor_id: str | None) -> None:
        async with self._lock:
            profile = siren.profiles.get(cause if cause in PROFILE_CAUSES else "intrusion", {})
            active = self._active.get(siren.id)
            if active is None:
                active = self._active[siren.id] = _Active()
            for cancel in active.timers:
                cancel()
            active.timers.clear()

            # Device settings first, but a failure here must not keep the siren quiet.
            for key, entity_id, saved_attr, touched_attr in (
                (CONF_TONE, siren.tone_entity, "saved_tone", "touched_tone"),
                (CONF_VOLUME, siren.volume_entity, "saved_volume", "touched_volume"),
            ):
                value = profile.get(key)
                if value and entity_id:
                    if not getattr(active, touched_attr):
                        setattr(active, saved_attr, self._read(entity_id))
                        setattr(active, touched_attr, True)
                    await self._set_value(siren, entity_id, value)

            ok = await self._switch(siren, siren.control, True)
            if siren.light and not (cause == "gas" and self._gas_is_flammable(sensor_id)):
                await self._switch(siren, siren.light, True)  # no switching near flammable gas
            if not ok:
                self.last_start[siren.id] = {"name": siren.name, "result": "failed", "at": self.manager._wall()}
                return
            state = self.hass.states.get(siren.control)
            verified = bool(state and state.state == "on")
            self.last_start[siren.id] = {"name": siren.name, "result": "confirmed" if verified else "sent", "at": self.manager._wall()}
            self.manager.publish("siren_started", siren=siren.name, cause=cause, verified=verified)
            active.timers.append(async_call_later(self.hass, siren.max_duration, self._timeout(siren)))
            if siren.repeat_every > 0:
                active.timers.append(
                    async_call_later(self.hass, siren.repeat_every, self._repeat(siren, cause, sensor_id))
                )

    def _timeout(self, siren: Siren):
        @callback
        def fire(_now: datetime) -> None:
            self.hass.async_create_task(self._async_stop(siren, "max_duration"))

        return fire

    def _repeat(self, siren: Siren, cause: str, sensor_id: str | None):
        @callback
        def fire(_now: datetime) -> None:
            self.hass.async_create_task(self._async_resend(siren, cause, sensor_id))

        return fire

    async def _async_resend(self, siren: Siren, cause: str, sensor_id: str | None) -> None:
        """For sirens that stop by themselves: switch them on again."""
        async with self._lock:
            active = self._active.get(siren.id)
            if active is None:  # stopped in the meantime
                return
            await self._switch(siren, siren.control, True)
            active.timers.append(
                async_call_later(self.hass, siren.repeat_every, self._repeat(siren, cause, sensor_id))
            )

    async def _async_stop(self, siren: Siren, reason: str) -> None:
        async with self._lock:
            active = self._active.pop(siren.id, None)
            if active is None:
                return  # it never started, or it already stopped (max_duration)
            for cancel in active.timers:
                cancel()
            await self._switch(siren, siren.control, False)
            if siren.light:
                await self._switch(siren, siren.light, False)
            if active.touched_tone and active.saved_tone and siren.tone_entity:
                await self._set_value(siren, siren.tone_entity, active.saved_tone)
            if active.touched_volume and active.saved_volume and siren.volume_entity:
                await self._set_value(siren, siren.volume_entity, active.saved_volume)
            self.manager.publish("siren_stopped", siren=siren.name, reason=reason)

    # ----------------------------------------------------------------- test

    async def async_test(self, name: str | None, duration: float) -> int:
        """Sound the siren(s) briefly, to check that they respond."""
        if self.manager.any_triggered:
            raise ServiceValidationError(translation_domain=DOMAIN, translation_key="alarm_active")
        chosen = [s for s in self.sirens if name in (None, s.name)]
        for siren in chosen:
            if await self._switch(siren, siren.control, True):
                async_call_later(self.hass, duration, self._test_off(siren))
        return len(chosen)

    def _test_off(self, siren: Siren):
        @callback
        def fire(_now: datetime) -> None:
            if not self.manager.any_triggered:  # a real alarm keeps its siren
                self.hass.async_create_task(self._switch(siren, siren.control, False))

        return fire
