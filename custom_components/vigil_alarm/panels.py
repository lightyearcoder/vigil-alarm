"""The register of control points (panels, later tablets) and the profile each one gets.

The panel is a dumb terminal: Vigil decides what it may do. A registered panel is found by its id, which is
also the `source` of its calls. What a registered panel may do is enforced here, in the manager, and every
refusal is logged. Calls with a source that is not registered (a phone, an automation) are not touched.

Be honest about what this protects: `source` is plain text, so Vigil cannot prove that a call really comes
from that panel. The profile protects against mistakes and against a panel that should not have certain
buttons, not against someone who can already call services. The real protection is the code, the lockout,
the encrypted connection of the panel and the access rules of Home Assistant itself. `unlocked` in the profile
is a hint for the screen, not security: the names of the sensors are simply not in the profile while it is false.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any

from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_call_later, async_track_time_interval
from homeassistant.helpers.storage import Store

from .const import (
    CONF_ALLOWED_MODES,
    CONF_BLOCKED,
    CONF_CAN_BYPASS,
    CONF_CAN_DISARM,
    CONF_CAN_SILENCE,
    CONF_HA_USER,
    CONF_LANGUAGE,
    CONF_PANEL_ID,
    CONF_SENSOR_LIST,
    CONF_UNLOCK_SECONDS,
    DEFAULT_UNLOCK_SECONDS,
    DOMAIN,
    PANEL_OFFLINE_SECONDS,
    CONF_SCREEN_OFF_ON_ALARM,
    CONF_SCREEN_OFF_SECONDS,
    DEFAULT_SCREEN_OFF_ON_ALARM,
    DEFAULT_SCREEN_OFF_SECONDS,
    PROFILE_VERSION,
    SUBENTRY_PANEL,
)
from .credentials import code_matches, find_user_by_code
from .items import Item, items_of

if TYPE_CHECKING:
    from .manager import VigilManager

CHECK_INTERVAL = 30  # seconds between looks at whether the panels are connected
# What a call does -> the permission it needs.
_NEEDS = {"disarm": CONF_CAN_DISARM, "bypass": CONF_CAN_BYPASS, "unbypass": CONF_CAN_BYPASS,
          "silence": CONF_CAN_SILENCE, "acknowledge": CONF_CAN_SILENCE}


def profile_object_id(panel_id: str) -> str:
    """The entity id (without `sensor.`) of the profile of a panel. The firmware works it out from its own
    device name, so it needs no setting: `vigil-panel-garage` reads `sensor.vigil_panel_garage_profile`."""
    return f"{panel_id.replace('-', '_')}_profile"


# The entities of a panel that report what it is (by the name given in the firmware).
REPORTED = {"Hardware ID": "hardware", "Capabilities": "capabilities", "Firmware version": "firmware",
            "Profile version": "profile_supported"}


def admin_bucket(panel_id: str) -> str:
    """The name of the lockout timer of the administrator code of one panel."""
    return f"admin:{panel_id}"


class PanelRegistry:
    def __init__(self, hass: HomeAssistant, manager: VigilManager) -> None:
        self.hass = hass
        self.manager = manager
        self._unlocked: dict[str, CALLBACK_TYPE] = {}  # panel id -> cancel the timer; only in memory
        self._since: dict[str, float] = {}  # panel id -> when we first saw it without a connection
        self._offline: set[str] = set()
        self._unsub: CALLBACK_TYPE | None = None
        # Tablets with the Vigil card say hello now and then. Only a tablet that has ever done so is watched:
        # a tablet with Home Assistant's own alarm card cannot say anything. The ids are kept in storage; when
        # they were last seen is not, so after a restart every one of them gets ten minutes again.
        self._seen: dict[str, float] = {}
        self._cards: set[str] = set()
        self._store: Store[dict[str, Any]] = Store(hass, 1, f"{DOMAIN}.tablets.{manager.entry.entry_id}")

    async def async_load(self) -> None:
        saved = await self._store.async_load() or {}
        now = self.manager._wall()
        self._cards = {str(p) for p in saved.get("cards") or []}
        self._seen = {pid: now for pid in self._cards}

    async def async_flush(self) -> None:
        if self._cards:
            await self._store.async_save({"cards": sorted(self._cards)})

    def hello(self, panel: Item) -> None:
        """The Vigil card of a tablet is open: it is there. Remembered, so a tablet that stops is reported."""
        pid = panel.data[CONF_PANEL_ID]
        self._seen[pid] = self.manager._wall()
        if pid not in self._cards:
            self._cards.add(pid)
            self._store.async_delay_save(lambda: {"cards": sorted(self._cards)}, 1)

    def profile_entity_id(self, panel: Item) -> str | None:
        registry = er.async_get(self.hass)
        return registry.async_get_entity_id(
            "sensor", DOMAIN, f"{self.manager.entry.entry_id}_{panel.subentry_id}_profile"
        )


    # -------------------------------------------------------------- register
    def items(self) -> list[Item]:
        return [s for s in items_of(self.manager.entry).values() if s.subentry_type == SUBENTRY_PANEL]

    def get(self, source: str | None) -> Item | None:
        if not source:
            return None
        return next((p for p in self.items() if p.data.get(CONF_PANEL_ID) == source), None)

    def for_user(self, user_id: str | None) -> Item | None:
        """The tablet that is bound to this Home Assistant user, if any."""
        if not user_id:
            return None
        return next((p for p in self.items() if p.data.get(CONF_HA_USER) == user_id), None)

    def source_for(self, source: str | None, user_id: str | None) -> str | None:
        """Who is calling. The user of a call is put there by Home Assistant and cannot be forged, so a tablet
        bound to that user wins over whatever `source` text the call carries."""
        tablet = self.for_user(user_id)
        return tablet.data[CONF_PANEL_ID] if tablet else source

    def ids(self) -> set[str]:
        return {p.data[CONF_PANEL_ID] for p in self.items()}

    # --------------------------------------------------------------- profile
    def allowed_modes(self, panel: Item) -> list[str]:
        modes = list(self.manager.config.modes)
        chosen = panel.data.get(CONF_ALLOWED_MODES) or modes
        return [m for m in modes if m in chosen]

    def language(self, panel: Item) -> str:
        lang = panel.data.get(CONF_LANGUAGE) or str(self.hass.config.language)
        return "nl" if lang.startswith("nl") else "en"

    def unlocked(self, panel_id: str) -> bool:
        return panel_id in self._unlocked

    def profile(self, panel: Item) -> dict[str, Any]:
        """What the panel gets to read. Never a code, hash, salt or key; sensor names only when it may show them."""
        d = panel.data
        pid = d[CONF_PANEL_ID]
        blocked = bool(d.get(CONF_BLOCKED))
        unlocked = self.unlocked(pid) and not blocked
        sensor_list = d.get(CONF_SENSOR_LIST, "code")
        visible = not blocked and (sensor_list == "always" or (sensor_list == "code" and unlocked))
        registry = er.async_get(self.hass)
        alarm = registry.async_get_entity_id("alarm_control_panel", DOMAIN, self.manager.entry.entry_id)
        snap = self.manager.snapshot()
        profile: dict[str, Any] = {
            "profile_version": PROFILE_VERSION,
            "name": panel.title,
            "panel_id": pid,
            "language": self.language(panel),
            "alarm": [alarm] if alarm else [],
            "allowed_modes": [] if blocked else self.allowed_modes(panel),
            "can_disarm": not blocked and bool(d.get(CONF_CAN_DISARM, True)),
            "can_bypass": not blocked and bool(d.get(CONF_CAN_BYPASS, True)),
            "can_silence": not blocked and bool(d.get(CONF_CAN_SILENCE, True)),
            "sensor_list": sensor_list,
            "unlock_seconds": int(d.get(CONF_UNLOCK_SECONDS, DEFAULT_UNLOCK_SECONDS)),
            "blocked": blocked,
            "code_arm_required": self.manager.code_arm_required,
            "screen_off_seconds": int(self.manager.entry.data.get(CONF_SCREEN_OFF_SECONDS, DEFAULT_SCREEN_OFF_SECONDS)),
            "screen_off_on_alarm": bool(self.manager.entry.data.get(CONF_SCREEN_OFF_ON_ALARM, DEFAULT_SCREEN_OFF_ON_ALARM)),
            "has_admin_code": bool(d.get("code_hash")),
            "unlocked": unlocked,
            "kind": "tablet" if d.get(CONF_HA_USER) else "esphome",
            "modes_mask": 0 if blocked else sum({"home": 1, "away": 2, "night": 4}[m] for m in self.allowed_modes(panel)),
            "open_count": len(snap["open_now"]),
            "faults_count": len(snap["faults"]),
            "problems_count": len(snap["problems"]),
            "open_now_text": "",
            "open_sensors_text": "",
            "faults_text": "",
            "sensors": "",
        }
        if visible:
            profile["open_now_text"] = ", ".join(snap["open_now"])
            profile["open_sensors_text"] = ", ".join(snap["open_sensors"])
            profile["faults_text"] = ", ".join(snap["faults"])
            profile["sensors"] = snap["panel_sensors"]
        return profile

    # ------------------------------------------------------------ enforcement
    def check(self, source: str | None, action: str, mode: str | None = None) -> Item | None:
        """Refuse (and log) a call the profile of a registered panel does not allow. Returns the panel."""
        panel = self.get(source)
        if panel is None:
            return None
        reason: str | None = None
        if panel.data.get(CONF_BLOCKED):
            reason = "blocked"
        elif action == "arm" and mode not in self.allowed_modes(panel):
            reason = "mode"
        elif (need := _NEEDS.get(action)) and not panel.data.get(need, True):
            reason = need
        if reason is None:
            return panel
        self.manager.publish("panel_refused", source=source, panel=panel.title, action=action, reason=reason)
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="panel_blocked" if reason == "blocked" else "panel_not_allowed",
            translation_placeholders={"panel": panel.title, "action": action},
        )

    # ---------------------------------------------------------------- unlocking
    @callback
    def _changed(self) -> None:
        from .manager import SIGNAL_UPDATE

        async_dispatcher_send(self.hass, SIGNAL_UPDATE.format(self.manager.entry.entry_id))

    @callback
    def unlock(self, panel: Item, by: str | None = None) -> None:
        """Show the list of sensors and the information pages for `unlock_seconds`. Never disarms."""
        pid = panel.data[CONF_PANEL_ID]
        if panel.data.get(CONF_BLOCKED):
            raise ServiceValidationError(translation_domain=DOMAIN, translation_key="panel_blocked",
                                         translation_placeholders={"panel": panel.title, "action": "unlock"})
        self.lock(pid, quiet=True)
        seconds = int(panel.data.get(CONF_UNLOCK_SECONDS, DEFAULT_UNLOCK_SECONDS))

        @callback
        def expire(_now: datetime) -> None:
            self._unlocked.pop(pid, None)
            self._changed()

        self._unlocked[pid] = async_call_later(self.hass, seconds, expire)
        self.manager.publish("panel_unlocked", source=pid, panel=panel.title, by=by or "code")
        self._changed()

    @callback
    def lock(self, panel_id: str, quiet: bool = False) -> None:
        if cancel := self._unlocked.pop(panel_id, None):
            cancel()
            if not quiet:
                self._changed()

    async def async_unlock_with_code(self, code: str | None, source: str | None, scope: str = "info") -> None:
        """The panel sends a code; Vigil checks it and unlocks.

        `info`: the installer code of that panel. `sensors`: any Vigil user code, or the installer code; it counts
        on the same lockout timer as every other user code of the panel."""
        panel = self.check(source, "unlock_panel")
        if panel is None:
            raise ServiceValidationError(translation_domain=DOMAIN, translation_key="unknown_panel")
        if scope == "sensors":
            await self._unlock_for_sensors(panel, code, source)
            return
        if not panel.data.get("code_hash"):
            raise ServiceValidationError(translation_domain=DOMAIN, translation_key="no_admin_code")
        if not code:
            raise ServiceValidationError(translation_domain=DOMAIN, translation_key="code_required")
        pid = panel.data[CONF_PANEL_ID]
        bucket = admin_bucket(pid)
        lockout = self.manager.lockout
        if lockout.refusal(source, bucket=bucket):
            raise self.manager.lock_error(source, bucket)
        if not await self.hass.async_add_executor_job(code_matches, code, panel.data):
            locked = lockout.record_failure(source, bucket=bucket)
            if locked:
                self.manager.publish_lock(locked, source, "unlock_panel")
            self.manager.publish("code_rejected", source=source, action="unlock_panel")
            if locked:
                raise self.manager.lock_error(source, bucket, started=locked)
            raise ServiceValidationError(translation_domain=DOMAIN, translation_key="invalid_code")
        lockout.record_success(source, bucket=bucket)
        self.unlock(panel)

    async def _unlock_for_sensors(self, panel: Item, code: str | None, source: str | None) -> None:
        manager = self.manager
        if not manager.users and not panel.data.get("code_hash"):
            raise ServiceValidationError(translation_domain=DOMAIN, translation_key="no_admin_code")
        if not code:
            raise ServiceValidationError(translation_domain=DOMAIN, translation_key="code_required")
        if manager.lockout.refusal(source):
            raise manager.lock_error(source)
        user = await self.hass.async_add_executor_job(find_user_by_code, code, manager.users) if manager.users else None
        installer = user is None and bool(panel.data.get("code_hash")) and await self.hass.async_add_executor_job(
            code_matches, code, panel.data)
        if user is None and not installer:
            locked = manager.lockout.record_failure(source)
            if locked:
                manager.publish_lock(locked, source, "unlock_panel")
            manager.publish("code_rejected", source=source, action="unlock_panel")
            if locked:
                raise manager.lock_error(source, started=locked)
            raise ServiceValidationError(translation_domain=DOMAIN, translation_key="invalid_code")
        manager.lockout.record_success(source)
        self.unlock(panel, by=user.title if user else "installer")

    def clear_lock(self, panel: Item, by: str | None = None) -> bool:
        """Lift the stored lockout of this panel (both its user-code timer and its administrator-code timer)."""
        pid = panel.data[CONF_PANEL_ID]
        cleared = self.manager.lockout.clear(pid) | self.manager.lockout.clear(admin_bucket(pid))
        self.manager.publish("panel_lock_cleared", source=pid, panel=panel.title, by=by or "-")
        self._changed()
        return cleared

    # ------------------------------------------------------------ connection
    def _connected(self, panel_id: str) -> bool | None:
        """Is the ESPHome device of this panel reachable? None: no ESPHome entry with that name."""
        if panel_id in self._cards:  # a tablet: has its card said hello lately?
            return self.manager._wall() - self._seen.get(panel_id, 0) < PANEL_OFFLINE_SECONDS
        for config_entry in self.hass.config_entries.async_entries("esphome"):
            if config_entry.data.get("device_name") != panel_id:
                continue
            registry = er.async_get(self.hass)
            states = [
                self.hass.states.get(e.entity_id)
                for e in er.async_entries_for_config_entry(registry, config_entry.entry_id)
                if not e.disabled
            ]
            known = [s for s in states if s is not None]
            return any(s.state != "unavailable" for s in known) if known else False
        return None

    def reported(self, panel_id: str) -> dict[str, str]:
        """What the panel says about itself (hardware, capabilities, firmware and the profile version it
        understands), read from its ESPHome sensors. Empty if there is nothing to read."""
        out: dict[str, str] = {}
        registry = er.async_get(self.hass)
        for config_entry in self.hass.config_entries.async_entries("esphome"):
            if config_entry.data.get("device_name") != panel_id:
                continue
            for ent in er.async_entries_for_config_entry(registry, config_entry.entry_id):
                key = REPORTED.get(ent.original_name or "")
                state = self.hass.states.get(ent.entity_id)
                if key and state is not None and state.state not in ("unknown", "unavailable", ""):
                    out[key] = state.state
        return out

    def problems(self) -> list[dict[str, str]]:
        """Things to put right on a panel: firmware that does not understand this profile.
        Only for panels that report; a panel that does not report is a connection matter."""
        found = []
        for panel in self.items():
            if panel.data.get(CONF_HA_USER) or panel.data.get(CONF_BLOCKED):
                continue
            pid = panel.data[CONF_PANEL_ID]
            seen = self.reported(pid)
            if not seen:
                continue
            if seen.get("profile_supported") != str(PROFILE_VERSION):
                found.append({"code": "panel_firmware", "name": panel.title,
                              "seen": seen.get("profile_supported", "?"), "wanted": str(PROFILE_VERSION)})
        return found

    def start(self) -> None:
        self._since.clear()
        self._offline.clear()
        self._unsub = async_track_time_interval(self.hass, self._tick, timedelta(seconds=CHECK_INTERVAL))
        self._tick(None)

    def stop(self) -> None:
        if self._unsub:
            self._unsub()
            self._unsub = None
        for pid in list(self._unlocked):
            self.lock(pid, quiet=True)

    @callback
    def _tick(self, _now: datetime | None) -> None:
        now = self.manager._wall()
        watched: set[str] = set()
        for panel in self.items():
            pid = panel.data[CONF_PANEL_ID]
            if panel.data.get(CONF_BLOCKED):
                continue  # blocked: taken out of service on purpose
            if panel.data.get(CONF_HA_USER) and pid not in self._cards:
                continue  # a tablet that never said hello has no Vigil card: nothing to watch
            watched.add(pid)
            if self._connected(pid):
                self._since.pop(pid, None)
                if pid in self._offline:
                    self._offline.discard(pid)
                    self.manager.publish("panel_online", source=pid, panel=panel.title)
                continue
            # An ESPHome device is given ten minutes from the moment we saw it gone; for a tablet the ten minutes
            # are the time since its card last said hello.
            since = now - PANEL_OFFLINE_SECONDS if pid in self._cards else self._since.setdefault(pid, now)
            if now - since >= PANEL_OFFLINE_SECONDS and pid not in self._offline:
                self._offline.add(pid)
                self.manager.publish("panel_offline", source=pid, panel=panel.title,
                                     minutes=PANEL_OFFLINE_SECONDS // 60)
        for pid in set(self._since) - watched:
            del self._since[pid]
        self._offline &= watched

    def issues(self) -> dict[str, tuple[str, dict[str, str]]]:
        """For the Repairs: one for every panel that has been out of reach too long."""
        entry_id = self.manager.entry.entry_id
        titles = {p.data[CONF_PANEL_ID]: p.title for p in self.items()}
        return {f"{entry_id}_panel_offline_{pid}": ("panel_offline", {"name": titles[pid]})
                for pid in sorted(self._offline) if pid in titles}

    def status(self) -> list[dict[str, Any]]:
        """What the admin panel shows per register entry (the live part)."""
        lockout = self.manager.lockout.status()
        permanent = self.manager.lockout.permanent()
        out = []
        for panel in self.items():
            pid = panel.data[CONF_PANEL_ID]
            out.append({
                "id": panel.subentry_id,
                "panel_id": pid,
                "kind": "tablet" if panel.data.get(CONF_HA_USER) else "esphome",
                "connected": self._connected(pid) if (pid in self._cards or not panel.data.get(CONF_HA_USER)) else None,
                "card": pid in self._cards,
                "offline": pid in self._offline,
                "unlocked": self.unlocked(pid),
                "locked_for": max(lockout.get(pid, 0), lockout.get(admin_bucket(pid), 0)),
                "locked_permanent": pid in permanent or admin_bucket(pid) in permanent,
                "reported": {} if panel.data.get(CONF_HA_USER) else self.reported(pid),
            })
        return out
