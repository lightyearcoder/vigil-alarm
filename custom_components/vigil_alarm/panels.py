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

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any

from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_call_later, async_track_time_interval
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import (
    CONF_ALLOWED_MODES,
    MODES,
    MODE_BITS,
    CONF_BLOCKED,
    CONF_KEY_HASH,
    CONF_CAN_BYPASS,
    CONF_CAN_DISARM,
    CONF_CAN_SILENCE,
    CONF_HA_USER,
    CONF_LANGUAGE,
    CONF_PANEL_ID,
    CONF_SENSOR_LIST,
    CONF_WATCH,
    CONF_UNLOCK_SECONDS,
    DEFAULT_UNLOCK_SECONDS,
    DOMAIN,
    PANEL_OFFLINE_SECONDS,
    CONF_SCREEN_OFF_ON_ALARM,
    CONF_DEFAULT_PARTITION,
    CONF_PARTITION_RETURN_SECONDS,
    DEFAULT_PARTITION_RETURN_SECONDS,
    ALL_PARTITIONS,
    CONF_SCREEN_OFF_SECONDS,
    DEFAULT_SCREEN_OFF_ON_ALARM,
    DEFAULT_SCREEN_OFF_SECONDS,
    PROFILE_VERSION,
    PRIMARY_PARTITION,
    SUBENTRY_PANEL,
)
from .vigil_core import aggregate
from .credentials import code_matches, find_user_by_code
from .items import Item, items_of, save_stored, stored_items
from .languages import FALSE_ALARM, language_of

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


def _ha_state(state: str) -> str:
    """The state as Home Assistant calls it (the engine says armed_custom, Home Assistant armed_custom_bypass)."""
    return "armed_custom_bypass" if state == "armed_custom" else state


class PanelRegistry:
    def __init__(self, hass: HomeAssistant, manager: VigilManager) -> None:
        self.hass = hass
        self.manager = manager
        self._selected: dict[str, str] = {}  # panel id -> the partition it shows when that is not its default; only in memory
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
    def allowed_partitions(self, panel: Item) -> list[str]:
        """The partitions this panel may use, in the order of the installation (all of them when none is chosen)."""
        return self.manager.allowed_partitions(panel, list(self.manager.partitions))

    def allowed_modes(self, panel: Item, partition: str | None = None) -> list[str]:
        """The modes the panel may arm in a partition (the first one it may use when none is given)."""
        default = self.default_partition(panel)
        pid = partition or (default if default != ALL_PARTITIONS else (self.allowed_partitions(panel) or [PRIMARY_PARTITION])[0])
        part = self.manager.partitions.get(pid) or self.manager.partitions[PRIMARY_PARTITION]
        modes = list(part.config.modes)
        chosen = panel.data.get(CONF_ALLOWED_MODES) or modes
        return [m for m in modes if m in chosen]

    def default_partition(self, panel: Item) -> str:
        """The partition the panel shows first: its choice (an id, or "all" when it may use more than one), else the
        first one it may use."""
        allowed = self.allowed_partitions(panel) or [PRIMARY_PARTITION]
        want = panel.data.get(CONF_DEFAULT_PARTITION)
        if want == ALL_PARTITIONS and len(allowed) > 1:
            return ALL_PARTITIONS
        return want if want in allowed else allowed[0]

    def partition_for(self, source: str | None, partition: str | None) -> str | None:
        """The partition a call is for: the one it names; none named from a registered panel or tablet means the
        partition that panel starts on, so a panel that may only use the garage never ends up at the house."""
        if partition:
            return partition
        panel = self.get(source)
        return self.default_partition(panel) if panel is not None else None

    def selected(self, panel: Item) -> str:
        """What the panel shows now: what it chose last (an id, or "all"), as long as it may still use that."""
        allowed = self.allowed_partitions(panel) or [PRIMARY_PARTITION]
        want = self._selected.get(panel.data[CONF_PANEL_ID])
        if want == ALL_PARTITIONS and len(allowed) > 1:
            return ALL_PARTITIONS
        return want if want in allowed else self.default_partition(panel)

    def select(self, source: str | None, partition: str) -> None:
        """A panel that can switch tells Vigil which partition it shows; the profile follows."""
        panel = self.get(source)
        allowed = self.allowed_partitions(panel) if panel is not None else []
        if panel is None or not (partition in allowed or (partition == ALL_PARTITIONS and len(allowed) > 1)):
            raise ServiceValidationError(translation_domain=DOMAIN, translation_key="unknown_panel")
        pid = panel.data[CONF_PANEL_ID]
        if partition == self.default_partition(panel):
            self._selected.pop(pid, None)
        else:
            self._selected[pid] = partition
        self.manager.notify_changed()

    def return_seconds(self) -> int:
        """After this long without touch a screen that can switch goes back to its default partition (0: never)."""
        return int(self.manager.entry.data.get(CONF_PARTITION_RETURN_SECONDS, DEFAULT_PARTITION_RETURN_SECONDS))

    def partitions_of(self, panel: Item) -> list[dict[str, Any]]:
        """What the panel may use: for each partition its name, its alarm entity and the modes it may arm."""
        entry_id = self.manager.entry.entry_id
        registry = er.async_get(self.hass)
        out = []
        for pid in self.allowed_partitions(panel):
            part = self.manager.partitions[pid]
            uid = entry_id if part.primary else f"{entry_id}_partition_{pid}"
            out.append({
                "id": pid, "name": part.name,
                "alarm": registry.async_get_entity_id("alarm_control_panel", DOMAIN, uid),
                "modes": self.allowed_modes(panel, pid),
            })
        return out

    def language(self, panel: Item) -> str:
        return language_of(panel.data.get(CONF_LANGUAGE) or self.hass.config.language)

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
        shown = self.partitions_of(panel)
        default = self.default_partition(panel)
        chosen = self.selected(panel) if shown else default
        allowed = [e["id"] for e in shown]
        ids = allowed if chosen == ALL_PARTITIONS else [chosen]  # what the screen shows now
        first = next((e for e in shown if e["id"] == default), shown[0] if shown else None)  # an older firmware knows one
        alarm = first["alarm"] if first else None
        snaps = {pid: self.manager.snapshot(pid) for pid in ids}
        snap = next(iter(snaps.values()))
        total = lambda key: sum(len(sn[key]) for sn in snaps.values())  # noqa: E731
        joined = lambda key: ", ".join(dict.fromkeys(x for sn in snaps.values() for x in sn[key]))  # noqa: E731
        states = {pid: self.manager.partitions[pid].engine.state for pid in ids}
        view = aggregate(states) if len(ids) > 1 else None
        busy = min((sn["delay_end"] for sn in snaps.values() if sn["delay_end"]), default=None)
        raised = next((sn for sn in snaps.values() if self.manager.partitions[sn["partition"]].engine.state == "triggered"), snap)
        modes = [m for m in MODES if any(m in self.allowed_modes(panel, q) for q in ids)]
        every = aggregate({e["id"]: self.manager.partitions[e["id"]].engine.state for e in shown})
        rows = [f"{e['id']}|{e['name'].replace('|', '/')}|{_ha_state(self.manager.partitions[e['id']].engine.state)}" for e in shown]
        if len(shown) > 1:
            rows.append(f"{ALL_PARTITIONS}||{_ha_state(every.ha_state)}{'|mixed' if every.mixed else ''}")
        profile: dict[str, Any] = {
            "profile_version": PROFILE_VERSION,
            "name": panel.title,
            "panel_id": pid,
            "language": self.language(panel),
            "alarm": [alarm] if alarm else [],  # the partition it starts on; an older firmware knows no other
            "partitions": [] if blocked else shown,
            "default_partition": default,
            "selected_partition": chosen,
            "partition_return_seconds": self.return_seconds(),
            "partition_total": len(self.manager.partitions),
            # For a firmware that can switch: "id|name|state" per partition it may use, then "all||state" when it may
            # use more than one. The state is what the chip is coloured by.
            "partition_list": "" if blocked else "\n".join(rows),
            # What the screen shows, of the partition on screen (or added up for "all"): the firmware reads these
            # instead of the alarm entity, so it needs no entity per partition.
            "view_state": _ha_state(view.ha_state if view else states.get(ids[0], "disarmed")),
            "view_mixed": bool(view and view.mixed),
            "view_mode": "" if view or not snap["mode"] else snap["mode"],
            "view_delay_left": round(max(0.0, busy - dt_util.utcnow().timestamp()), 1) if busy else "",
            "view_changed_by": self.manager.changed_by or "",
            "view_changed_via": self.manager.changed_via or "",
            "view_cause": raised["cause"] or "",
            "view_cause_sensor": raised["cause_sensor"] or "",
            "allowed_modes": [] if blocked else modes,
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
            "modes_mask": 0 if blocked else sum(MODE_BITS[m] for m in modes),
            "open_count": sum(sn["open_now_count"] for sn in snaps.values()),
            "faults_count": total("faults"),
            "problems_count": len(snap["problems"]),
            "open_now_text": "",
            "open_sensors_text": "",
            "faults_text": "",
            "last_alarm_text": "",
            "bypassed_text": "",
            "sensors": "",
        }
        # Per partition the panel may use: what it needs to show that partition (names only when it may show them).
        for entry in profile["partitions"]:
            psnap = self.manager.snapshot(entry["id"])
            entry.update({
                "open_count": len(psnap["open_now"]), "faults_count": len(psnap["faults"]),
                "open_now_text": ", ".join(psnap["open_now"]) if visible else "",
                "open_sensors_text": ", ".join(psnap["open_sensors"]) if visible else "",
                "faults_text": ", ".join(psnap["faults"]) if visible else "",
                "bypassed_text": ", ".join(psnap["bypassed_sensors"]) if visible else "",
            })
        profile["sensors_all"] = self.manager.panel_rows([e["id"] for e in shown]) if visible and len(shown) > 1 else ""
        if visible:
            profile["open_now_text"] = joined("open_now")
            profile["open_sensors_text"] = joined("open_sensors")
            profile["faults_text"] = joined("faults")
            profile["sensors"] = self.manager.panel_rows(ids) if len(ids) > 1 else snap["panel_sensors"]
            profile["last_alarm_text"] = self._last_alarm_text(profile["language"])
            profile["bypassed_text"] = joined("bypassed_sensors")
        return profile

    def _last_alarm_text(self, language: str) -> str:
        """The alarm memory in one line for the panel: "14:03 Front door > Hall > Living room". Names of sensors,
        so it follows the same rule as the sensor list."""
        view = self.manager.alarmmemory.view()
        if not view or not view.get("started"):
            return ""
        when = dt_util.as_local(dt_util.utc_from_timestamp(view["started"])).strftime("%H:%M")
        names = [str(step["name"]) for step in view["path"] if step.get("name")]
        where = f" {view['partition_name']}:" if view.get("partition_name") else ""  # only with more than one partition
        text = when + where + (" " + " > ".join(names[-4:]) if names else (" " + str(view["sensor_name"]) if view.get("sensor_name") else ""))
        if view.get("cancelled"):
            text += f" ({FALSE_ALARM[language_of(language)]})"
        return text

    # ------------------------------------------------------------ enforcement
    def check(self, source: str | None, action: str, mode: str | None = None, partition: str | None = None) -> Item | None:
        """Refuse (and log) a call the profile of a registered panel does not allow. Returns the panel."""
        panel = self.get(source)
        if panel is None:
            return None
        reason: str | None = None
        if panel.data.get(CONF_BLOCKED):
            reason = "blocked"
        elif partition and partition not in self.allowed_partitions(panel):
            reason = "partition"
        elif action == "arm" and mode not in self.allowed_modes(panel, partition):
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

    # ------------------------------------------------------------------- key
    @staticmethod
    def _key_digest(key: str) -> str:
        return hashlib.sha256(key.encode()).hexdigest()

    def has_key(self, panel: Item) -> bool:
        return bool(panel.data.get(CONF_KEY_HASH))

    def verify_key(self, source: str | None, key: str | None, user_id: str | None) -> None:
        """A registered ESPHome panel that has a key must send it with every call. A call that names such a panel
        without the right key is refused (and logged): `source` is only text, the key is what proves the call
        comes from the device. A tablet is told apart by its Home Assistant user and needs none; a panel without a
        key is treated as before."""
        panel = self.get(source)
        if panel is None or not panel.data.get(CONF_KEY_HASH) or self.for_user(user_id):
            return
        if key and hmac.compare_digest(self._key_digest(key), panel.data[CONF_KEY_HASH]):
            return
        self.manager.publish("panel_refused", source=source, panel=panel.title, action="call", reason="key")
        raise ServiceValidationError(
            translation_domain=DOMAIN, translation_key="panel_key_wrong", translation_placeholders={"panel": panel.title},
        )

    def create_key(self, panel: Item, by: str | None = None) -> str:
        """A new key for an ESPHome panel (the old one stops working at once). Returned once; only its digest is kept."""
        if panel.data.get(CONF_HA_USER):
            raise ServiceValidationError(translation_domain=DOMAIN, translation_key="panel_not_allowed",
                                         translation_placeholders={"panel": panel.title, "action": "key"})
        key = secrets.token_hex(16)
        self._store_key(panel, self._key_digest(key))
        self.manager.publish("panel_key_created", source=panel.data[CONF_PANEL_ID], panel=panel.title, **({"by": by} if by else {}))
        return key

    def remove_key(self, panel: Item, by: str | None = None) -> bool:
        if not panel.data.get(CONF_KEY_HASH):
            return False
        self._store_key(panel, None)
        self.manager.publish("panel_key_removed", source=panel.data[CONF_PANEL_ID], panel=panel.title, **({"by": by} if by else {}))
        return True

    def _store_key(self, panel: Item, digest: str | None) -> None:
        working = stored_items(self.manager.entry)
        data = dict(working[panel.subentry_id]["data"])
        if digest:
            data[CONF_KEY_HASH] = digest
        else:
            data.pop(CONF_KEY_HASH, None)
        working[panel.subentry_id] = {**working[panel.subentry_id], "data": data}
        save_stored(self.hass, self.manager.entry, working)

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
        # `user` is the person whose code it was; the installer code of the panel belongs to no one in particular
        person = by if by not in (None, "code", "installer") else None
        self.manager.publish("panel_unlocked", source=pid, panel=panel.title, by=by or "code", **({"user": person} if person else {}))
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
        """Things to put right on a panel: no key yet, or firmware that does not understand this profile.
        Only for panels that report; a panel that does not report is a connection matter."""
        found = []
        for panel in self.items():
            if panel.data.get(CONF_HA_USER) or panel.data.get(CONF_BLOCKED):
                continue
            pid = panel.data[CONF_PANEL_ID]
            if not self.has_key(panel):
                found.append({"code": "panel_no_key", "name": panel.title})
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
            if not panel.data.get(CONF_WATCH, True):
                continue  # the administrator does not want to hear when this one is away (a phone, say)
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
                "watched": bool(panel.data.get(CONF_WATCH, True)),
                "unlocked": self.unlocked(pid),
                "locked_for": max(lockout.get(pid, 0), lockout.get(admin_bucket(pid), 0)),
                "locked_permanent": pid in permanent or admin_bucket(pid) in permanent,
                "reported": {} if panel.data.get(CONF_HA_USER) else self.reported(pid),
            })
        return out
