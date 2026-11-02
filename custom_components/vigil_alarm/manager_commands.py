"""What the manager does when someone arms, disarms, bypasses, silences or acknowledges: the commands."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from homeassistant.core import Context, callback
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import (
    async_call_later,
)

from .const import (
    CONF_ABORT_SECONDS,
    CONF_ALLOWED_MODES,
    CONF_CHIME_ENTITY,
    CONF_CHIME_SECONDS,
    CONF_MAY_BYPASS,
    CONF_MAY_BYPASS_TAMPER,
    DEFAULT_ABORT_SECONDS,
    DEFAULT_CHIME_SECONDS,
    DOMAIN,
    PRIMARY_PARTITION,
)
from .credentials import find_user_and_kind
from .errors import VigilError
from .items import Item

# The log keeps its name, so a `logger:` setting for the manager still applies.
from .manager_config import SIGNAL_EVENT, Partition, partition_data

_LOGGER = logging.getLogger(f"{__package__}.manager")


class CommandsMixin:
    """The commands of VigilManager (arm, disarm, bypass, silence, chime)."""


    async def _operator(self, source: str | None, user_id: str | None, action: str) -> str | None:
        """Who is calling? Returns the source (the panel id of a registered account wins over a made-up text).

        Once an account is registered, a Home Assistant account that is neither registered nor an administrator
        is refused here, before any code is looked at and without counting towards a lockout. A call without a
        user (an automation, a script, an ESPHome panel) is not touched: those are your own."""
        source = self.panels.source_for(source, user_id)
        if not user_id or self.panels.for_user(user_id) or not self.only_registered:
            return source
        account = await self.hass.auth.async_get_user(user_id)
        if account is not None and not account.is_admin and not account.system_generated:
            self.publish("user_refused", user=account.name, source=source, action=action)
            raise VigilError(translation_domain=DOMAIN, translation_key="user_not_registered")
        return source

    async def _authenticate(
        self, code: str | None, *, required: bool, source: str | None = None, action: str | None = None,
    ) -> Item | None:
        """Find the user for a code. No users configured: everything is allowed."""
        if not self.users:
            return None
        if not code:
            if required:
                raise VigilError(
                    translation_domain=DOMAIN, translation_key="code_required"
                )
            return None
        if self.lockout.refusal(source):  # before hashing: a locked control point also costs no CPU
            raise self.lock_error(source)
        user, duress = await self.hass.async_add_executor_job(find_user_and_kind, code, self.users)
        self.auth_duress = duress and user is not None
        if user is not None:
            self.lockout.record_success(source)
            if duress:  # works like the normal code, and tells the channels quietly
                self.publish("duress_used", quiet=True, user=user.title, source=source, action=action)
        else:
            if locked := self.lockout.record_failure(source):
                self.publish_lock(locked, source, action)
            # Never log the code itself; the source (for example a panel) and the action are enough.
            self.publish("code_rejected", source=source, action=action)
            if locked:  # this wrong code started a lock: say so at once, not only at the next try
                raise self.lock_error(source, started=locked)
            raise VigilError(translation_domain=DOMAIN, translation_key="invalid_code")
        return user

    def lock_error(self, source: str | None, bucket: str | None = None, started=None) -> VigilError:
        """The error for a locked control point: for good, or for so many more minutes (rounded up)."""
        if started is not None:
            permanent, seconds = started.minutes is None, (started.minutes or 0) * 60
        else:
            permanent, seconds = self.lockout.is_permanent(source, bucket), self.lockout.remaining(source, bucket)
        return VigilError(
            translation_domain=DOMAIN,
            translation_key="code_locked_permanent" if permanent else "code_locked",
            translation_placeholders={"minutes": str(max(1, -(-int(seconds) // 60)))},
        )

    def publish_lock(self, locked, source: str | None, action: str | None) -> None:
        """Tell that a lock has just started: for a while, or for good."""
        if locked.minutes is None:
            self.publish("code_locked_permanent", source=source, action=action, timer=locked.bucket)
        else:
            self.publish("code_locked", source=source, action=action, timer=locked.bucket, minutes=locked.minutes)
        self.notify_changed()  # the panel shows the lock at once, without waiting for the next try

    def _actor(self, user: Item | None, source: str | None) -> str | None:
        """Who or what did it: the user, the control point (a panel), or both. The two parts are remembered, so
        `changed_by` (the user) and `changed_via` (the panel or device) can be told apart."""
        name = user.title if user else None
        combined = (f"{name} ({source})" if name else source) if source else name
        if combined:
            self._actor_parts[combined] = (name, source)
        return combined

    def _sensor_names(self, ids: list[str]) -> str:
        return ", ".join(self._sensor_name.get(z, z) for z in ids) or "-"

    def arm_blockers(self, mode: str, *, sync: bool = True, partition: str | None = None) -> list[dict[str, Any]]:
        """What stops arming `mode` now, with the name of the sensor: the answer to "why can't I arm?".
        `sync=False` takes the engine as it is (the live view must not trigger a sync of its own)."""
        if sync:
            self._sync()
        return [
            {**b, "name": self._sensor_names([b["sensor"]]) if b["sensor"] else "",
             "entity_id": self._sensor_entity.get(b["sensor"]) if b["sensor"] else None}
            for b in self.partition(partition).engine.arm_check(mode)
        ]

    def _check_partition_right(self, part: Partition, user: Item | None) -> None:
        if user is not None and part.id not in self.allowed_partitions(user, list(self.partitions)):
            raise VigilError(
                translation_domain=DOMAIN, translation_key="partition_not_allowed",
                translation_placeholders={"user": user.title, "partition": part.name},
            )

    def _targets(self, partition: str | None, user: Item | None, source: str | None, action: str,
                 mode: str | None = None) -> list[Partition]:
        """The partitions an arm or disarm applies to: one, or all of them (`partition` "all")."""
        if partition == "all":
            if not self.multiple:
                return [self.partitions[PRIMARY_PARTITION]]
            allowed = self.allowed_partitions(user, list(self.partitions))
            panel = self.panels.get(source)
            if panel is not None:
                allowed = [p for p in allowed if p in self.panels.allowed_partitions(panel)]
            return [self.partitions[p] for p in allowed]
        part = self.partition(partition)
        self.panels.check(source, action, mode, part.id)
        return [part]

    async def async_arm(
        self, mode: str, code: str | None, source: str | None = None, user_id: str | None = None,
        *, bypass_open: bool = False, partition: str | None = None,
    ) -> None:
        """Arm. With `bypass_open` what stops it (an open tamper contact, a sensor that does not answer) is bypassed
        first: for someone who may bypass, with the same rules as bypassing by hand, and never a fire or gas sensor.

        `partition`: the id of one partition (none: the first), or "all": every partition the caller may use that is
        disarmed and has this mode. Nothing is armed unless all of them can be."""
        self.walktest.stop("stopped")  # arming ends a walk test
        source = await self._operator(source, user_id, "arm")
        if not self.ready:
            raise VigilError(translation_domain=DOMAIN, translation_key="not_ready")
        partition = self.panels.partition_for(source, partition)
        everywhere = partition == "all"
        first = self.partition(None if everywhere else partition)
        if not everywhere and mode not in first.config.modes:
            raise VigilError(
                translation_domain=DOMAIN,
                translation_key="mode_not_enabled",
                translation_placeholders={"mode": mode},
            )
        if not everywhere:
            self.panels.check(source, "arm", mode, first.id)
        panel = self.panels.check(source, "bypass", None, None if everywhere else first.id) if bypass_open else None
        # From a registered panel a bypass always needs a code, like bypassing by hand.
        user = await self._authenticate(
            code, required=self.code_arm_required or panel is not None, source=source, action="arm"
        )
        if everywhere:
            targets = [p for p in self._targets("all", user, source, "arm", mode)
                       if mode in p.config.modes and p.engine.state == "disarmed"]
            if not targets:
                raise VigilError(
                    translation_domain=DOMAIN, translation_key="mode_not_enabled",
                    translation_placeholders={"mode": mode},
                )
        else:
            self._check_partition_right(first, user)
            targets = [first]
        if user is not None:
            for part in targets:
                allowed = user.data.get(CONF_ALLOWED_MODES) or list(part.config.modes)
                if mode not in allowed:
                    raise VigilError(
                        translation_domain=DOMAIN,
                        translation_key="mode_not_allowed",
                        translation_placeholders={"user": user.title, "mode": mode},
                    )
        name = self._actor(user, source)
        self._sync()
        bypassed: list[tuple[Partition, str]] = []
        try:
            if bypass_open:
                is_admin = user_id is not None and await self.async_is_admin_id(user_id)
                for part in targets:
                    blockers = part.engine.arm_check(mode)
                    if blockers and not is_admin and user is not None and not user.data.get(CONF_MAY_BYPASS, True):
                        raise VigilError(translation_domain=DOMAIN, translation_key="bypass_not_allowed")
                    for b in blockers:
                        if b["sensor"] and self.config.sensors[b["sensor"]].cls == "tamper" and not is_admin \
                                and (user is None or not user.data.get(CONF_MAY_BYPASS_TAMPER, False)):
                            raise VigilError(translation_domain=DOMAIN, translation_key="tamper_bypass_not_allowed")
                    if all(b["bypassable"] for b in blockers):  # one that cannot be bypassed: it is refused as usual
                        for b in blockers:
                            if self._bypass_everywhere(b["sensor"], name, part):
                                bypassed.append((part, b["sensor"]))
            # All or nothing: when one partition cannot arm, none is armed.
            refusal = None
            if len(targets) > 1:
                blocked = [(part, part.engine.arm_check(mode)) for part in targets]
                blocked = [(part, found) for part, found in blocked if found]
                if blocked:
                    part, found = blocked[0]
                    sensors = [b["sensor"] for _p, f in blocked for b in f if b["sensor"]]
                    refusal = (found[0]["reason"], sensors)
            ok = refusal is None
            if ok:
                for part in targets:
                    ok = part.engine.arm(mode, user=name) and ok
        except VigilError:
            for part, sid in bypassed:
                self._unbypass_everywhere(sid, name)
            raise
        if not ok:
            for part, sid in bypassed:  # it did not start after all: put them back
                self._unbypass_everywhere(sid, name)
        self._after()
        if not ok:
            if refusal is None:
                event = next(e for e in reversed(targets[0].engine.events) if e["type"] == "arm_refused")
                refusal = (event["reason"], event["sensors"])
            raise VigilError(
                translation_domain=DOMAIN,
                translation_key="arm_refused",
                translation_placeholders={
                    "reason": refusal[0],
                    "sensors": self._sensor_names(refusal[1]),
                },
            )

    def _bypass_everywhere(self, sensor_id: str, name: str | None, part: Partition | None = None) -> bool:
        """Bypass a sensor in every partition that has it (a safety sensor is in all of them)."""
        done = False
        for p in self.partitions.values():
            if sensor_id in p.config.sensors:
                done = p.engine.bypass(sensor_id, user=name) or done
        return done

    def _unbypass_everywhere(self, sensor_id: str, name: str | None) -> None:
        for p in self.partitions.values():
            if sensor_id in p.config.sensors:
                p.engine.unbypass(sensor_id, user=name)

    async def async_check_code(self, code: str | None, source: str | None = None, user_id: str | None = None) -> None:
        """Is this a valid code? Counts as a try for the lockout. For a panel that hides things behind a code."""
        source = await self._operator(source, user_id, "check_code")
        self.panels.check(source, "check_code")
        await self._authenticate(code, required=True, source=source, action="check_code")

    async def async_disarm(
        self, code: str | None, source: str | None = None, user_id: str | None = None, *, partition: str | None = None,
    ) -> None:
        """Disarm one partition (none: the first) or, with "all", every partition the caller may use.

        An alarm from a safety sensor is one alarm for the whole house: disarming a partition that is in it ends it
        in every partition that is in it."""
        source = await self._operator(source, user_id, "disarm")
        partition = self.panels.partition_for(source, partition)
        part = self.partition(None if partition == "all" else partition)
        self.panels.check(source, "disarm", None, None if partition == "all" else part.id)
        user = await self._authenticate(code, required=True, source=source, action="disarm")
        duress = self.auth_duress
        self._sync()
        if partition == "all":
            targets = self._targets("all", user, source, "disarm")
        else:
            self._check_partition_right(part, user)
            targets = [part]
            if part.engine.state == "triggered" and part.engine.cause != "intrusion":
                targets += [p for p in self.partitions.values()
                            if p is not part and p.engine.state == "triggered" and p.engine.cause != "intrusion"]
        cancelled = not duress and any(self._within_abort_window(p) for p in targets)
        name = self._actor(user, source)
        for target in targets:
            target.engine.disarm(user=name)
        if cancelled:
            self.alarmmemory.mark_cancelled()
            self.publish("alarm_cancelled", user=name, source=source)
        self._after()

    def _within_abort_window(self, part: Partition | None = None) -> bool:
        """Is this a disarm soon enough after the siren went off to call it a false alarm?"""
        seconds = int(self.entry.data.get(CONF_ABORT_SECONDS, DEFAULT_ABORT_SECONDS))
        engine = (part or self.partitions[PRIMARY_PARTITION]).engine
        if seconds <= 0 or engine.state != "triggered" or engine.cause != "intrusion":
            return False
        started = self.alarmmemory.started
        return bool(self.alarmmemory.recording and started and self._wall() - started <= seconds)

    # ----------------------------------------------------------------- chime

    @callback
    def _chime(self, sensor_id: str) -> None:
        """A door or window with the chime opened while the alarm is off: a short sound. No alarm, no message and no
        line in the log; the event entity gets it, so an automation can do more (play a sound on a speaker)."""
        part = self.partition_of_sensor(sensor_id)
        if part.engine.state != "disarmed" or not self.ready:
            return
        now = self._wall()
        if now - self._chime_last.get(sensor_id, 0) < 3:  # a contact that flickers rings once
            return
        self._chime_last[sensor_id] = now
        async_dispatcher_send(
            self.hass, SIGNAL_EVENT.format(self.entry.entry_id),
            {"t": now, "type": "chime", "sensor": sensor_id, "sensor_name": self._sensor_name.get(sensor_id, sensor_id),
             "partition": part.id},
        )
        pdata = partition_data(self.entry, part.id)
        if entity_id := pdata.get(CONF_CHIME_ENTITY) or self.entry.data.get(CONF_CHIME_ENTITY):
            self.hass.async_create_task(self._async_ring(entity_id))

    async def _async_ring(self, entity_id: str) -> None:
        domain = entity_id.split(".")[0]
        try:
            if domain in ("button", "input_button"):
                await self.hass.services.async_call(domain, "press", {"entity_id": entity_id}, blocking=True)
            elif domain == "script":
                await self.hass.services.async_call("script", "turn_on", {"entity_id": entity_id}, blocking=True)
            else:
                await self.hass.services.async_call(domain, "turn_on", {"entity_id": entity_id}, blocking=True)

                @callback
                def off(_now: datetime) -> None:
                    self.hass.async_create_task(
                        self.hass.services.async_call(domain, "turn_off", {"entity_id": entity_id})
                    )

                seconds = float(self.entry.data.get(CONF_CHIME_SECONDS, DEFAULT_CHIME_SECONDS))
                async_call_later(self.hass, seconds, off)
        except Exception as err:  # noqa: BLE001 - a chime that fails must never matter
            _LOGGER.warning("Chime via %s failed: %s", entity_id, err)

    async def async_clear_alarm_memory(self, source: str | None = None, user: str | None = None) -> None:
        """Forget the last alarm. No code: it only wipes a note, it changes nothing in the alarm."""
        if self.alarmmemory.clear():
            self.publish("alarm_memory_cleared", user=user, source=source)
            self._after()

    async def async_bypass(
        self, sensor_id: str, code: str | None, *, is_admin: bool, bypass: bool, source: str | None = None,
        user_id: str | None = None,
    ) -> None:
        source = await self._operator(source, user_id, "bypass" if bypass else "unbypass")
        if sensor_id not in self.config.sensors:
            raise VigilError(translation_domain=DOMAIN, translation_key="unknown_sensor")
        sensor = self.config.sensors[sensor_id]
        action = "bypass" if bypass else "unbypass"
        panel = self.panels.check(source, action)
        # Like arming: a code is only needed when arming needs one (`code_arm_required`). From a registered
        # panel a code is always needed: that is part of the standard profile.
        user = await self._authorize(
            code, is_admin, required=self.code_arm_required or panel is not None, source=source,
            action="bypass" if bypass else "unbypass",
        )
        # Putting a sensor back follows the same rules as bypassing it: who may bypass it may restore it.
        if not is_admin and user is not None and not user.data.get(CONF_MAY_BYPASS, True):
            raise VigilError(translation_domain=DOMAIN, translation_key="bypass_not_allowed")
        if sensor.cls == "tamper" and not is_admin:
            if user is None or not user.data.get(CONF_MAY_BYPASS_TAMPER, False):
                raise VigilError(
                    translation_domain=DOMAIN, translation_key="tamper_bypass_not_allowed"
                )
        name = self._actor(user, source)
        self._sync()
        if bypass:
            ok = self._bypass_everywhere(sensor_id, name)
        else:
            self._unbypass_everywhere(sensor_id, name)
            ok = True
        self._after()
        if not ok:
            raise VigilError(
                translation_domain=DOMAIN, translation_key="sensor_not_bypassable"
            )

    async def _authorize(
        self, code: str | None, is_admin: bool, *, required: bool = True,
        source: str | None = None, action: str | None = None,
    ) -> Item | None:
        """An administrator in the UI, or a user with a valid code (when one is needed)."""
        if not is_admin:
            return await self._authenticate(code, required=required, source=source, action=action)
        if code:
            return await self._authenticate(code, required=False, source=source, action=action)
        return None

    async def async_silence(
        self, code: str | None, *, is_admin: bool, source: str | None = None, user_id: str | None = None
    ) -> None:
        """Stop the sirens; the alarm itself stays triggered."""
        source = await self._operator(source, user_id, "silence")
        self.panels.check(source, "silence")
        user = await self._authorize(code, is_admin, source=source, action="silence")
        name = self._actor(user, source)
        self.sirens.silence()
        self.publish("alarm_silenced", user=name)

    async def async_acknowledge(
        self, code: str | None, *, is_admin: bool, source: str | None = None, user_id: str | None = None
    ) -> None:
        """Confirm that the alarm has been seen: pending escalations are cancelled."""
        source = await self._operator(source, user_id, "acknowledge")
        self.panels.check(source, "acknowledge")
        user = await self._authorize(code, is_admin, source=source, action="acknowledge")
        name = self._actor(user, source)
        self.notifier.cancel_escalations()
        self.publish("alarm_acknowledged", user=name)

    async def async_is_admin_id(self, user_id: str) -> bool:
        if self.panels.for_user(user_id):  # a tablet is never an administrator for Vigil
            return False
        user = await self.hass.auth.async_get_user(user_id)
        return bool(user and user.is_admin)

    async def async_is_admin(self, context: Context | None) -> bool:
        """Calls from the UI carry a user; automations and scripts do not."""
        if context is None or not context.user_id:
            return False
        if self.panels.for_user(context.user_id):  # a tablet is never an administrator for Vigil
            return False
        user = await self.hass.auth.async_get_user(context.user_id)
        return bool(user and user.is_admin)

    def sensor_id_for_entity(self, entity_id: str) -> str | None:
        for sid, eid in self._sensor_entity.items():
            if eid == entity_id:
                return sid
        return None

