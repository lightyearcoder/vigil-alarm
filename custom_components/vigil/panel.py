"""The admin panel: a sidebar page to see and edit the whole configuration.

The panel only talks to this module (websocket commands, admin only). The
rules are the same as in the config flows: both use `editing`.
"""

from __future__ import annotations

from pathlib import Path
from types import MappingProxyType
from typing import Any

import voluptuous as vol

from homeassistant.components import frontend, panel_custom, websocket_api
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .items import Item, items_of, new_id as new_item_id, save_stored, stored, stored_items
from .const import (
    CONF_BATTERY_ENTITY,
    CONF_CODE_HASH,
    CONF_CODE_SALT,
    CONF_MODES,
    CONF_SENSORS,
    DOMAIN,
    MODES,
    NOTIFICATION_CATEGORIES,
    SIREN_CAUSES,
    PROFILE_CAUSES,
    SUBENTRY_RULE,
    SUBENTRY_NOTIFICATION,
    SUBENTRY_SIREN,
    SUBENTRY_USER,
    SUBENTRY_SENSOR,
    SUBENTRY_SENSOR_GROUP,
    CONF_SENSOR_GROUPS,
    SUGGEST_FOR,
)
from .editing import EditError, _TrialEntry, async_prepare, notify_services
from .manager import SIGNAL_UPDATE, build_config
from .presets import siren_preset_ids, siren_suggestion
from .vigil_core import ConfigError
from .vigil_core.model import AT_ARM_OPEN, CLASSES, GAS_TYPES, ON_UNAVAILABLE, SENSOR_TYPES

PANEL_URL = "vigil"
STATIC_URL = "/vigil_static/vigil-panel.js"
# The names the panel uses, and the subentry types they are stored under.
TYPE_OF = {
    "sensor": SUBENTRY_SENSOR,
    "sensor_group": SUBENTRY_SENSOR_GROUP,
    "rule": SUBENTRY_RULE,
    "user": SUBENTRY_USER,
    "notification": SUBENTRY_NOTIFICATION,
    "siren": SUBENTRY_SIREN,
}
KINDS = tuple(TYPE_OF)
_DATA_KEY = f"{DOMAIN}_panel"
_STATIC_KEY = f"{DOMAIN}_panel_static"


# --------------------------------------------------------------- form schema


def _f(key: str, type_: str, **kw: Any) -> dict[str, Any]:
    return {"key": key, "type": type_, **kw}


def form_schema(modes: list[str]) -> dict[str, list[dict[str, Any]]]:
    """Describe the forms; the panel renders them (labels live in the panel)."""
    intrusion = {"cls": ["intrusion"]}
    return {
        "sensor": [
            _f("name", "text", required=True),
            _f("entity_id", "entity", domains=["binary_sensor"], required=True),
            _f("cls", "select", options=list(CLASSES), default="intrusion", required=True),
            _f("type", "select", options=list(SENSOR_TYPES), default="instant", show_if=intrusion),
            _f("sensor_groups", "sensor_groups", default=[], required=True, show_if=intrusion),
            _f("at_arm_open", "select", options=list(AT_ARM_OPEN), default="bypass", show_if=intrusion),
            _f("entry_delay", "number", unit="s", min=0, max=600, show_if=intrusion),
            _f("gas_type", "select", options=list(GAS_TYPES), default="other", show_if={"cls": ["gas"]}),
            _f("on_unavailable", "select", options=["default", *ON_UNAVAILABLE], default="default"),
            _f(CONF_BATTERY_ENTITY, "entity", domains=["sensor"]),
        ],
        "sensor_group": [
            _f("name", "text", required=True),
            _f("modes", "multiselect", options=modes, default=[], required=True),
            _f("suggest_for", "select", options=["", *SUGGEST_FOR], default=""),
        ],
        "rule": [
            _f("name", "text", required=True),
            _f("sensors", "sensors", required=True),
            _f("required", "number", default=2, min=2, max=10, required=True),
            _f("window", "number", default=60, unit="s", min=0, max=3600, required=True),
            _f("escalate", "boolean", default=False),
        ],
        "user": [
            _f("name", "text", required=True),
            _f("code", "password"),
            _f("tags", "tags", default=[]),
            _f("allowed_modes", "multiselect", options=modes, default=[]),
            _f("may_bypass_tamper", "boolean", default=False),
        ],
        "notification": [
            _f("name", "text", required=True),
            _f("service", "notify", required=True),
            _f("categories", "multiselect", options=list(NOTIFICATION_CATEGORIES),
               default=["alarm", "pending", "fault", "technical"], required=True),
            _f("delay", "number", default=0, unit="s", min=0, max=3600),
            _f("priority", "boolean", default=False),
        ],
        "siren": [
            _f("name", "text", required=True),
            _f("preset", "preset"),  # not stored: fills the fields below for a known device
            _f("control", "entity", domains=["siren", "switch", "light"], required=True),
            _f("causes", "multiselect", options=list(SIREN_CAUSES), default=list(SIREN_CAUSES), required=True),
            _f("max_duration", "number", default=180, unit="s", min=0, max=3600),
            _f("repeat_every", "number", default=0, unit="s", min=0, max=3600),
            _f("light", "entity", domains=["switch", "light"]),
            _f("tone_entity", "entity", domains=["select", "input_select"]),
            _f("volume_entity", "entity", domains=["number", "input_number", "select", "input_select"]),
            _f("battery_entity", "entity", domains=["sensor"]),
            _f("power_entity", "entity", domains=["sensor", "select"]),
            _f("power_battery_value", "text"),
            *[_f(f"{cause}.tone", "text", group=cause) for cause in PROFILE_CAUSES],
            *[_f(f"{cause}.volume", "text", group=cause) for cause in PROFILE_CAUSES],
        ],
    }


def settings_schema() -> list[dict[str, Any]]:
    return [
        _f("modes", "multiselect", options=list(MODES), required=True),
        *[_f(f"exit_delay_{m}", "number", unit="s", min=0, max=3600, show_if={"modes": [m]}) for m in MODES],
        _f("default_entry_delay", "number", unit="s", min=0, max=3600),
        _f("trigger_time", "number", unit="s", min=0, max=86400),
        _f("battery_threshold", "number", unit="%", min=1, max=100),
        _f("code_arm_required", "boolean"),
    ]


# ------------------------------------------------------------- serialisation


def _public(sub: Item) -> dict[str, Any]:
    """What the panel may see of a subentry: never the hash or the salt of a code."""
    data = dict(sub.data)
    has_code = bool(data.pop(CONF_CODE_HASH, None))
    data.pop(CONF_CODE_SALT, None)
    data.pop("code_numeric", None)
    out = {"id": sub.subentry_id, "title": sub.title, "data": data}
    if sub.subentry_type == SUBENTRY_USER:
        out["has_code"] = has_code
    return out


def _entry_for(hass: HomeAssistant) -> ConfigEntry | None:
    entries = hass.config_entries.async_loaded_entries(DOMAIN)
    return entries[0] if entries else None


def _snapshot(hass: HomeAssistant, entry: ConfigEntry) -> dict[str, Any]:
    registry = er.async_get(hass)
    sensor_entities: dict[str, dict[str, str | None]] = {}
    for sid, sub in items_of(entry).items():
        if sub.subentry_type != SUBENTRY_SENSOR:
            continue
        sensor_entities[sid] = {
            "bypass": registry.async_get_entity_id("switch", DOMAIN, f"{entry.entry_id}_{sid}_bypass"),
            "status": registry.async_get_entity_id("sensor", DOMAIN, f"{entry.entry_id}_{sid}_status"),
        }
    return {
        "entry": {"id": entry.entry_id, "title": entry.title, "data": dict(entry.data)},
        "items": {
            kind: [_public(s) for s in items_of(entry).values() if s.subentry_type == TYPE_OF[kind]]
            for kind in KINDS
        },
        "forms": form_schema(list(entry.data.get(CONF_MODES, MODES))),
        "settings_form": settings_schema(),
        "sensor_entities": sensor_entities,
        "alarm_entity": registry.async_get_entity_id("alarm_control_panel", DOMAIN, entry.entry_id),
        "notify_services": notify_services(hass),
        "siren_presets": siren_preset_ids(),
    }


def _live(entry: ConfigEntry) -> dict[str, Any] | None:
    manager = getattr(entry, "runtime_data", None)
    if manager is None:  # reloading
        return None
    return {
        "state": manager.engine.state,
        "mode": manager.engine.mode,
        "sensors": {z: manager.engine.sensor_status(z) for z in manager.config.sensors},
        "problems": manager.supervisor.problems(),
    }


# --------------------------------------------------------- websocket commands


def _no_entry(connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    connection.send_error(msg["id"], "not_loaded", "Vigil Alarm is not set up or is not loaded")


@websocket_api.websocket_command({vol.Required("type"): "vigil/get"})
@websocket_api.require_admin
@callback
def ws_get(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    entry = _entry_for(hass)
    if entry is None:
        _no_entry(connection, msg)
        return
    connection.send_result(msg["id"], _snapshot(hass, entry))


@websocket_api.websocket_command({vol.Required("type"): "vigil/subscribe"})
@websocket_api.require_admin
@callback
def ws_subscribe(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    entry = _entry_for(hass)
    if entry is None:
        _no_entry(connection, msg)
        return

    @callback
    def push() -> None:
        live = _live(entry)
        if live is not None:
            connection.send_message(websocket_api.event_message(msg["id"], live))

    unsub = async_dispatcher_connect(hass, SIGNAL_UPDATE.format(entry.entry_id), push)
    connection.subscriptions[msg["id"]] = unsub
    connection.send_result(msg["id"])
    push()


@websocket_api.websocket_command(
    {vol.Required("type"): "vigil/siren_preset", vol.Required("preset"): str, vol.Optional("control"): str}
)
@websocket_api.require_admin
@callback
def ws_siren_preset(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    """Settings (and the entities found on the same device) for a known siren."""
    result = siren_suggestion(hass, msg["preset"], msg.get("control"))
    if result is None:
        connection.send_error(msg["id"], "not_found", "Unknown preset")
        return
    connection.send_result(msg["id"], result)


def _failure(err: EditError) -> dict[str, Any]:
    return {"ok": False, "errors": err.errors, "placeholders": err.placeholders}


@websocket_api.websocket_command(
    {
        vol.Required("type"): "vigil/save",
        vol.Required("kind"): vol.In(KINDS),
        vol.Optional("subentry_id"): str,
        vol.Required("data"): dict,
    }
)
@websocket_api.require_admin
@websocket_api.async_response
async def ws_save(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    entry = _entry_for(hass)
    if entry is None:
        _no_entry(connection, msg)
        return
    sub = None
    if msg.get("subentry_id"):
        sub = items_of(entry).get(msg["subentry_id"])
        if sub is None or sub.subentry_type != TYPE_OF[msg["kind"]]:
            connection.send_error(msg["id"], "not_found", "Unknown item")
            return
    try:
        title, data = await async_prepare(hass, entry, TYPE_OF[msg["kind"]], sub, msg["data"])
    except EditError as err:
        connection.send_result(msg["id"], _failure(err))
        return
    stored_all = stored_items(entry)
    new_id = sub.subentry_id if sub else new_item_id()
    stored_all[new_id] = stored(TYPE_OF[msg["kind"]], title, data)
    save_stored(hass, entry, stored_all)
    connection.send_result(msg["id"], {"ok": True, "id": new_id})


@websocket_api.websocket_command({vol.Required("type"): "vigil/delete", vol.Required("subentry_id"): str})
@websocket_api.require_admin
@websocket_api.async_response
async def ws_delete(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    entry = _entry_for(hass)
    if entry is None:
        _no_entry(connection, msg)
        return
    sub = items_of(entry).get(msg["subentry_id"])
    if sub is None:
        connection.send_error(msg["id"], "not_found", "Unknown item")
        return
    if sub.subentry_type == SUBENTRY_SENSOR:
        used = [
            g.title for g in items_of(entry).values()
            if g.subentry_type == SUBENTRY_RULE and sub.subentry_id in g.data.get(CONF_SENSORS, [])
        ]
        if used:
            connection.send_result(
                msg["id"], _failure(EditError({"base": "sensor_in_rule"}, {"rules": ", ".join(used)}))
            )
            return
    if sub.subentry_type == SUBENTRY_SENSOR_GROUP:
        users = [
            s.title for s in items_of(entry).values()
            if s.subentry_type == SUBENTRY_SENSOR and sub.subentry_id in s.data.get(CONF_SENSOR_GROUPS, [])
        ]
        if users:
            connection.send_result(
                msg["id"], _failure(EditError({"base": "sensor_group_in_use"}, {"sensors": ", ".join(users)}))
            )
            return
    stored_all = stored_items(entry)
    stored_all.pop(sub.subentry_id, None)
    save_stored(hass, entry, stored_all)
    connection.send_result(msg["id"], {"ok": True})


@websocket_api.websocket_command(
    {vol.Required("type"): "vigil/save_settings", vol.Required("data"): dict}
)
@websocket_api.require_admin
@websocket_api.async_response
async def ws_save_settings(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    entry = _entry_for(hass)
    if entry is None:
        _no_entry(connection, msg)
        return
    data = {k: v for k, v in msg["data"].items() if k in {f["key"] for f in settings_schema()}}
    if not data.get(CONF_MODES):
        connection.send_result(msg["id"], _failure(EditError({"modes": "no_modes"})))
        return
    try:
        build_config(_TrialEntry(entry, data))  # type: ignore[arg-type]
    except ConfigError as err:
        connection.send_result(msg["id"], _failure(EditError({"base": "invalid_config"}, {"error": str(err)})))
        return
    hass.config_entries.async_update_entry(entry, data=data)
    connection.send_result(msg["id"], {"ok": True})


@callback
def async_register_commands(hass: HomeAssistant) -> None:
    for command in (ws_get, ws_subscribe, ws_save, ws_delete, ws_save_settings, ws_siren_preset):
        websocket_api.async_register_command(hass, command)


# ------------------------------------------------------------- panel itself


async def async_register_panel(hass: HomeAssistant, version: str) -> None:
    if hass.data.get(_DATA_KEY):
        return
    if not hass.data.get(_STATIC_KEY):
        path = Path(__file__).parent / "frontend" / "vigil-panel.js"
        await hass.http.async_register_static_paths([StaticPathConfig(STATIC_URL, str(path), cache_headers=False)])
        hass.data[_STATIC_KEY] = True
    await panel_custom.async_register_panel(
        hass,
        frontend_url_path=PANEL_URL,
        webcomponent_name="vigil-panel",
        sidebar_title="Vigil Alarm",
        sidebar_icon="mdi:shield-home",
        module_url=f"{STATIC_URL}?v={version}",
        require_admin=True,
        embed_iframe=False,
    )
    hass.data[_DATA_KEY] = True


@callback
def async_remove_panel(hass: HomeAssistant) -> None:
    if hass.data.pop(_DATA_KEY, None):
        frontend.async_remove_panel(hass, PANEL_URL)
