"""The admin panel: its websocket commands (admin only). The rules are the same as in the config flows: both use `editing`."""

from __future__ import annotations

import json
from typing import Any

import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .about import async_about
from .backups import BackupError, export_payload
from .backups import capture as capture_config
from .backups import diff as diff_config
from .backups import mark_reason as mark_backup_reason
from .backups import read_payload as read_backup_payload
from .const import (
    ABORT_SECONDS_RANGE,
    BACKUP_VERSIONS_RANGE,
    CHIME_DOMAINS,
    CHIME_SECONDS_RANGE,
    CONF_ABORT_SECONDS,
    CONF_BACKUP_VERSIONS,
    CONF_CHIME_ENTITY,
    CONF_CHIME_SECONDS,
    CONF_COMPANION_OF,
    CONF_DEFAULT_ENTRY_DELAY,
    CONF_EXIT_DELAY,
    CONF_HEARTBEAT_INTERVAL,
    CONF_HEARTBEAT_URL,
    CONF_LOG_RETENTION_DAYS,
    CONF_MIN_CODE_LENGTH,
    CONF_MODES,
    CONF_PARTITION,
    CONF_PARTITION_NAME,
    CONF_PARTITION_RETURN_SECONDS,
    CONF_PARTITIONS,
    CONF_SCREEN_OFF_ON_ALARM,
    CONF_SCREEN_OFF_SECONDS,
    CONF_SELFTEST_AUTO,
    CONF_SELFTEST_HANDLERS,
    CONF_SENSOR_GROUPS,
    CONF_SENSORS,
    CONF_STARTUP_WAIT,
    CONF_TRIGGER_TIME,
    DEFAULT_ABORT_SECONDS,
    DEFAULT_BACKUP_VERSIONS,
    DEFAULT_CHIME_SECONDS,
    DEFAULT_HEARTBEAT_INTERVAL,
    DEFAULT_LOG_RETENTION_DAYS,
    DEFAULT_PARTITION_RETURN_SECONDS,
    DEFAULT_SCREEN_OFF_ON_ALARM,
    DEFAULT_SCREEN_OFF_SECONDS,
    DEFAULT_SELFTEST,
    DEFAULT_STARTUP_WAIT,
    DOMAIN,
    HEARTBEAT_INTERVAL_RANGE,
    LOCK_DEFAULTS,
    LOCK_TRIES_RANGE,
    LOCK_WAIT_RANGE,
    LOG_RETENTION_CEILING,
    LOG_RETENTION_FLOOR,
    MIN_CODE_LENGTH_CEILING,
    MIN_CODE_LENGTH_FLOOR,
    MODES,
    PARTITION_RETURN_RANGE,
    PRIMARY_PARTITION,
    SCREEN_OFF_RANGE,
    SELFTEST_RANGES,
    STARTUP_WAIT_RANGE,
    SUBENTRY_NOTIFICATION,
    SUBENTRY_PANEL,
    SUBENTRY_PARTITION,
    SUBENTRY_RULE,
    SUBENTRY_SENSOR,
    SUBENTRY_SENSOR_GROUP,
    SUBENTRY_SIREN,
)
from .dashboard import async_dashboard
from .discovery import async_discover, async_report
from .editing import EditError, _TrialEntry, async_prepare, companion_id, plan_companion
from .errors import VigilError
from .heartbeat import valid_url
from .items import Item, items_of, save_stored, stored, stored_items
from .items import new_id as new_item_id
from .languages import language_of
from .manager import SIGNAL_UPDATE, build_config, partition_ids
from .migration import ENTRY_VERSION
from .panel_forms import _EVENT_LABELS, _VERSION, KINDS, TYPE_OF, settings_schema
from .panel_state import _entry_for, _live, _snapshot
from .presets import siren_suggestion
from .readiness import (
    async_create_default_groups,
    async_readiness,
    phone_services,
    phone_title,
)
from .vigil_core import ConfigError

# --------------------------------------------------------- websocket commands


def _no_entry(connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    connection.send_error(msg["id"], "not_loaded", "Vigil Alarm is not set up or is not loaded")


@websocket_api.websocket_command({vol.Required("type"): "vigil_alarm/get"})
@websocket_api.require_admin
@websocket_api.async_response
async def ws_get(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    entry = _entry_for(hass)
    if entry is None:
        _no_entry(connection, msg)
        return
    connection.send_result(msg["id"], _snapshot(hass, entry, await hass.auth.async_get_users()))


@websocket_api.websocket_command({vol.Required("type"): "vigil_alarm/about"})
@websocket_api.require_admin
@websocket_api.async_response
async def ws_about(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    entry = _entry_for(hass)
    if entry is None:
        _no_entry(connection, msg)
        return
    counts = {
        kind: sum(1 for s in items_of(entry).values() if s.subentry_type == TYPE_OF[kind]) for kind in KINDS
    }
    live = _live(entry)
    connection.send_result(msg["id"], await async_about(hass, counts, live["state"] if live else None))


@websocket_api.websocket_command({vol.Required("type"): "vigil_alarm/discover"})
@websocket_api.require_admin
@callback
def ws_discover(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    """Sensors that could be added, from the entity registry. Nothing is saved."""
    entry = _entry_for(hass)
    if entry is None:
        _no_entry(connection, msg)
        return
    found = async_discover(hass, entry)
    manager = getattr(entry, "runtime_data", None)
    ignored = manager.new_sensors.ignored if manager is not None else set()
    for c in [*found["candidates"], *found["tamper_only"]]:
        c["ignored"] = c["entity_id"] in ignored
    connection.send_result(msg["id"], found)


@websocket_api.websocket_command(
    {vol.Required("type"): "vigil_alarm/discover_ignore", vol.Required("entity_ids"): [str], vol.Required("ignore"): bool}
)
@websocket_api.require_admin
@websocket_api.async_response
async def ws_discover_ignore(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    """Ignore entities in Find sensors (or bring them back). Nothing else changes."""
    entry = _entry_for(hass)
    manager = getattr(entry, "runtime_data", None) if entry else None
    if manager is None:
        _no_entry(connection, msg)
        return
    await manager.new_sensors.async_set_ignored(msg["entity_ids"], msg["ignore"])
    connection.send_result(msg["id"], {"ok": True})


@websocket_api.websocket_command({vol.Required("type"): "vigil_alarm/alarm_memory_clear"})
@websocket_api.require_admin
@websocket_api.async_response
async def ws_alarm_memory_clear(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    entry = _entry_for(hass)
    if entry is None:
        _no_entry(connection, msg)
        return
    user = connection.user.name if connection.user else None
    await entry.runtime_data.async_clear_alarm_memory("admin panel", user)
    connection.send_result(msg["id"], {"ok": True})


@websocket_api.websocket_command({vol.Required("type"): "vigil_alarm/new_sensors_dismiss"})
@websocket_api.require_admin
@websocket_api.async_response
async def ws_new_sensors_dismiss(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    """*Not now*: the new sensors found so far are not announced again."""
    entry = _entry_for(hass)
    manager = getattr(entry, "runtime_data", None) if entry else None
    if manager is None:
        _no_entry(connection, msg)
        return
    await manager.new_sensors.async_dismiss()
    connection.send_result(msg["id"], {"ok": True})


@websocket_api.websocket_command({vol.Required("type"): "vigil_alarm/practice", vol.Required("enable"): bool})
@websocket_api.require_admin
@callback
def ws_practice(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    """Practice mode on or off: the alarm works as usual, but no siren and no messages."""
    entry = _entry_for(hass)
    manager = getattr(entry, "runtime_data", None) if entry else None
    if manager is None:
        _no_entry(connection, msg)
        return
    try:
        manager.practice.start() if msg["enable"] else manager.practice.stop()
    except VigilError as err:
        connection.send_error(msg["id"], "refused", str(err))
        return
    connection.send_result(msg["id"], {"ok": True, "until": manager.practice.until})


@websocket_api.websocket_command({vol.Required("type"): "vigil_alarm/walktest", vol.Required("action"): vol.In(["start", "stop"])})
@websocket_api.require_admin
@callback
def ws_walktest(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    """Start or stop the walk test (walk along the sensors with the alarm off)."""
    entry = _entry_for(hass)
    manager = getattr(entry, "runtime_data", None) if entry else None
    if manager is None:
        _no_entry(connection, msg)
        return
    try:
        manager.walktest.start() if msg["action"] == "start" else manager.walktest.stop("stopped")
    except VigilError as err:
        connection.send_error(msg["id"], "refused", str(err))
        return
    connection.send_result(msg["id"], {"ok": True, **manager.walktest.status()})


@websocket_api.websocket_command({vol.Required("type"): "vigil_alarm/discover_report"})
@websocket_api.require_admin
@callback
def ws_discover_report(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    """The anonymous list testers can copy."""
    connection.send_result(msg["id"], async_report(hass))


@websocket_api.websocket_command({vol.Required("type"): "vigil_alarm/readiness"})
@websocket_api.require_admin
@callback
def ws_readiness(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    """What stops the alarm from protecting yet, or could make it better."""
    entry = _entry_for(hass)
    if entry is None:
        _no_entry(connection, msg)
        return
    connection.send_result(msg["id"], {"findings": async_readiness(hass, entry)})


@websocket_api.websocket_command({vol.Required("type"): "vigil_alarm/add_phone", vol.Required("service"): str})
@websocket_api.require_admin
@websocket_api.async_response
async def ws_add_phone(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    """A notification channel for a phone with the Home Assistant app, with the usual categories."""
    entry = _entry_for(hass)
    if entry is None:
        _no_entry(connection, msg)
        return
    if msg["service"] not in phone_services(hass, entry):
        connection.send_result(msg["id"], {"ok": False, "errors": {"service": "service_not_found"}, "placeholders": {}})
        return
    title = phone_title(msg["service"])
    raw = {"name": title, "services": [msg["service"]], "categories": ["alarm", "pending", "fault", "technical"], "delay": 0, "partitions": ["all"]}
    try:
        name, data = await async_prepare(hass, entry, SUBENTRY_NOTIFICATION, None, raw)
    except EditError as err:
        connection.send_result(msg["id"], _failure(err))
        return
    working = stored_items(entry)
    new_id = new_item_id()
    working[new_id] = stored(SUBENTRY_NOTIFICATION, name, data)
    save_stored(hass, entry, working)
    connection.send_result(msg["id"], {"ok": True, "id": new_id, "title": name})


@websocket_api.websocket_command(
    {vol.Required("type"): "vigil_alarm/log", vol.Optional("limit", default=200): vol.All(int, vol.Range(min=1, max=2000))}
)
@websocket_api.require_admin
@callback
def ws_log(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    """The newest entries of the event log, and what the event types are called."""
    entry = _entry_for(hass)
    if entry is None or getattr(entry, "runtime_data", None) is None:
        _no_entry(connection, msg)
        return
    log = entry.runtime_data.eventlog
    language = language_of(hass.config.language)
    connection.send_result(
        msg["id"],
        {"entries": log.recent(msg["limit"]), "total": len(log.entries), "labels": _EVENT_LABELS[language], "retention_days": log.retention_days},
    )


@websocket_api.websocket_command(
    {vol.Required("type"): "vigil_alarm/log_export", vol.Required("format"): vol.In(["jsonl", "csv"])}
)
@websocket_api.require_admin
@callback
def ws_log_export(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    """The whole log as a file: JSON Lines or CSV."""
    entry = _entry_for(hass)
    if entry is None or getattr(entry, "runtime_data", None) is None:
        _no_entry(connection, msg)
        return
    name, media_type, text = entry.runtime_data.eventlog.export(msg["format"])
    connection.send_result(msg["id"], {"filename": name, "media_type": media_type, "text": text})


@websocket_api.websocket_command({vol.Required("type"): "vigil_alarm/selftest"})
@websocket_api.require_admin
@callback
def ws_selftest(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    """When the quiet check and the siren test last ran, and when the next test is due."""
    entry = _entry_for(hass)
    if entry is None or getattr(entry, "runtime_data", None) is None:
        _no_entry(connection, msg)
        return
    connection.send_result(msg["id"], entry.runtime_data.selftest.status())


@websocket_api.websocket_command({vol.Required("type"): "vigil_alarm/heartbeat", vol.Optional("test", default=False): bool})
@websocket_api.require_admin
@websocket_api.async_response
async def ws_heartbeat(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    """The heartbeat's status (never the address). With test, call the address once first."""
    entry = _entry_for(hass)
    if entry is None or getattr(entry, "runtime_data", None) is None:
        _no_entry(connection, msg)
        return
    beat = entry.runtime_data.heartbeat
    if msg["test"]:
        await beat.ping()
    connection.send_result(msg["id"], beat.status())


def _panel_item(entry: ConfigEntry, item_id: str) -> Item | None:
    item = items_of(entry).get(item_id)
    return item if item is not None and item.subentry_type == SUBENTRY_PANEL else None


@websocket_api.websocket_command({vol.Required("type"): "vigil_alarm/tablet"})
@callback
def ws_tablet(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    """For the Vigil card on a tablet, and open to every user (the card is not for administrators only). It tells
    the card which panel of the register belongs to the logged-in user, and counts as the card saying hello,
    so Vigil can report a tablet that has gone quiet. It gives away no more than the profile entity does."""
    entry = _entry_for(hass)
    if entry is None or getattr(entry, "runtime_data", None) is None:
        connection.send_result(msg["id"], {"linked": False, "user": connection.user.name})
        return
    registry = entry.runtime_data.panels
    panel = registry.for_user(connection.user.id)
    alarm = er.async_get(hass).async_get_entity_id("alarm_control_panel", DOMAIN, entry.entry_id)
    if panel is None:
        connection.send_result(msg["id"], {"linked": False, "user": connection.user.name})
        return
    registry.hello(panel)
    connection.send_result(msg["id"], {
        "linked": True,
        "kind": "tablet",
        "user": connection.user.name,
        "panel_id": panel.data["panel_id"],
        "name": panel.title,
        "profile_entity": registry.profile_entity_id(panel),
        "alarm_entity": alarm,
        # What the card offers: the partitions this tablet may use, and (more than one) the entity for all of them.
        "partitions": registry.partitions_of(panel),
        "default_partition": registry.default_partition(panel),
        "return_seconds": registry.return_seconds(),
        "partition_total": len(registry.manager.partitions),
        "all_entity": er.async_get(hass).async_get_entity_id("alarm_control_panel", DOMAIN, f"{entry.entry_id}_all")
        if len(registry.allowed_partitions(panel)) > 1 else None,
    })


@websocket_api.websocket_command({vol.Required("type"): "vigil_alarm/panel_unlock", vol.Required("subentry_id"): str})
@websocket_api.require_admin
@callback
def ws_panel_unlock(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    """Unlock a panel from Home Assistant. Only here and never as an action: an action can be called by any
    user, automation or panel, so a stolen panel could unlock itself."""
    entry = _entry_for(hass)
    if entry is None or getattr(entry, "runtime_data", None) is None:
        _no_entry(connection, msg)
        return
    item = _panel_item(entry, msg["subentry_id"])
    if item is None:
        connection.send_error(msg["id"], "not_found", "Unknown panel")
        return
    try:
        entry.runtime_data.panels.unlock(item, by=connection.user.name)
    except Exception as err:  # a blocked panel is refused
        connection.send_error(msg["id"], "refused", str(err))
        return
    # The administrator unlocks the panel: a lock after wrong codes goes too, with its counts. (Not when a panel unlocks
    # itself with the installer code: that must never lift its own lock.)
    was_locked = False
    if entry.runtime_data.panels.is_locked(item):
        was_locked = entry.runtime_data.panels.clear_lock(item, by=connection.user.name)
    connection.send_result(msg["id"], {"ok": True, "was_locked": was_locked})


@websocket_api.websocket_command({vol.Required("type"): "vigil_alarm/panel_clear_lock", vol.Required("subentry_id"): str})
@websocket_api.require_admin
@callback
def ws_panel_clear_lock(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    """Lift the stored lockout (after wrong codes) of one panel. Only here, never as an action."""
    entry = _entry_for(hass)
    if entry is None or getattr(entry, "runtime_data", None) is None:
        _no_entry(connection, msg)
        return
    item = _panel_item(entry, msg["subentry_id"])
    if item is None:
        connection.send_error(msg["id"], "not_found", "Unknown panel")
        return
    connection.send_result(msg["id"], {"ok": True, "was_locked": entry.runtime_data.panels.clear_lock(item, by=connection.user.name)})


@websocket_api.websocket_command(
    {vol.Required("type"): "vigil_alarm/panel_key", vol.Required("subentry_id"): str, vol.Required("action"): vol.In(["create", "remove"])}
)
@websocket_api.require_admin
@callback
def ws_panel_key(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    """Make (or replace) the key of an ESPHome panel, or take it away. The key is shown once, here: Vigil keeps
    only a digest. Never an action: any user could call one."""
    entry = _entry_for(hass)
    if entry is None or getattr(entry, "runtime_data", None) is None:
        _no_entry(connection, msg)
        return
    item = _panel_item(entry, msg["subentry_id"])
    if item is None:
        connection.send_error(msg["id"], "not_found", "Unknown panel")
        return
    registry = entry.runtime_data.panels
    try:
        if msg["action"] == "create":
            connection.send_result(msg["id"], {"ok": True, "key": registry.create_key(item, by=connection.user.name), "panel_id": item.data["panel_id"]})
        else:
            connection.send_result(msg["id"], {"ok": True, "was_set": registry.remove_key(item, by=connection.user.name)})
    except Exception as err:  # a tablet has no key
        connection.send_error(msg["id"], "refused", str(err))


@websocket_api.websocket_command({vol.Required("type"): "vigil_alarm/dashboard"})
@websocket_api.require_admin
@callback
def ws_dashboard(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    """A dashboard with this installation's own entity ids, as text to paste."""
    entry = _entry_for(hass)
    if entry is None:
        _no_entry(connection, msg)
        return
    connection.send_result(msg["id"], {"yaml": async_dashboard(hass, entry)})


@websocket_api.websocket_command({vol.Required("type"): "vigil_alarm/create_default_groups", vol.Optional("partition"): str})
@websocket_api.require_admin
@callback
def ws_create_default_groups(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    """Add the usual sensor groups (doors and windows, motion) if they do not exist yet."""
    entry = _entry_for(hass)
    if entry is None:
        _no_entry(connection, msg)
        return
    partition = msg.get("partition") or PRIMARY_PARTITION
    if partition not in partition_ids(entry):
        connection.send_result(msg["id"], _failure(EditError({"partition": "unknown_partition"})))
        return
    connection.send_result(msg["id"], {"ok": True, "ids": async_create_default_groups(hass, entry, partition)})


@websocket_api.websocket_command({vol.Required("type"): "vigil_alarm/subscribe"})
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
    {vol.Required("type"): "vigil_alarm/siren_preset", vol.Required("preset"): str, vol.Optional("control"): str}
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
        vol.Required("type"): "vigil_alarm/save",
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
        if sub is None or sub.subentry_type != TYPE_OF[msg["kind"]] or sub.data.get(CONF_COMPANION_OF):
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
    if msg["kind"] in ("sensor", "siren"):  # the tamper contact that belongs to this sensor or siren follows it
        try:
            companion = plan_companion(hass, entry, new_id, title, data)
        except EditError as err:
            connection.send_result(msg["id"], _failure(err))
            return
        old = companion_id(entry, new_id)
        if companion is None:
            stored_all.pop(old, None)
        else:
            stored_all[old or new_item_id()] = stored(SUBENTRY_SENSOR, *companion)
    save_stored(hass, entry, stored_all)
    connection.send_result(msg["id"], {"ok": True, "id": new_id})


@websocket_api.websocket_command(
    {vol.Required("type"): "vigil_alarm/save_many", vol.Required("items"): [dict], vol.Optional("preview", default=False): bool}
)
@websocket_api.require_admin
@websocket_api.async_response
async def ws_save_many(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    """Add several new sensors at once: every check first, then one save and one reload.

    Each sensor is checked against the ones before it, so two with the same entity or name are
    refused. If one fails nothing is saved and the answer says which one (`index`).
    """
    entry = _entry_for(hass)
    if entry is None:
        _no_entry(connection, msg)
        return
    working = stored_items(entry)
    ids: list[str] = []
    for index, raw in enumerate(msg["items"]):
        trial = _TrialEntry(entry, entry.data)
        trial.options = {**entry.options, "items": working}
        try:
            title, data = await async_prepare(hass, trial, SUBENTRY_SENSOR, None, raw)  # type: ignore[arg-type]
            new_id = new_item_id()
            working[new_id] = stored(SUBENTRY_SENSOR, title, data)
            trial.options = {**entry.options, "items": working}
            companion = plan_companion(hass, trial, new_id, title, data)  # type: ignore[arg-type]
        except EditError as err:
            connection.send_result(msg["id"], {**_failure(err), "index": index})
            return
        if companion is not None:
            working[new_item_id()] = stored(SUBENTRY_SENSOR, *companion)
        ids.append(new_id)
    before = capture_config(entry)
    change = diff_config(before, {"data": before["data"], "options": {**before["options"], "items": json.loads(json.dumps(working))}})
    if ids and not msg["preview"]:
        save_stored(hass, entry, working)
    connection.send_result(msg["id"], {"ok": True, "ids": ids, "change": change})


@websocket_api.websocket_command({vol.Required("type"): "vigil_alarm/delete", vol.Required("subentry_id"): str})
@websocket_api.require_admin
@websocket_api.async_response
async def ws_delete(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    entry = _entry_for(hass)
    if entry is None:
        _no_entry(connection, msg)
        return
    sub = items_of(entry).get(msg["subentry_id"])
    if sub is None or sub.data.get(CONF_COMPANION_OF):  # a tamper contact is removed with its sensor
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
    if sub.subentry_type == SUBENTRY_PARTITION:
        inside = [
            s.title for s in items_of(entry).values()
            if s.subentry_type == SUBENTRY_SENSOR and s.data.get(CONF_PARTITION) == sub.subentry_id
        ]
        if inside:  # move them to another partition first: a sensor must never end up in none
            connection.send_result(
                msg["id"], _failure(EditError({"base": "partition_in_use"}, {"sensors": ", ".join(inside)}))
            )
            return
        groups = [
            g.title for g in items_of(entry).values()
            if g.subentry_type == SUBENTRY_SENSOR_GROUP and g.data.get(CONF_PARTITION) == sub.subentry_id
        ]
        if groups:
            connection.send_result(
                msg["id"], _failure(EditError({"base": "partition_has_groups"}, {"groups": ", ".join(groups)}))
            )
            return
    stored_all = stored_items(entry)
    stored_all.pop(sub.subentry_id, None)
    if sub.subentry_type == SUBENTRY_PARTITION:  # no list may keep pointing at it
        for item in stored_all.values():
            chosen = item.get("data", {}).get(CONF_PARTITIONS)
            if chosen and sub.subentry_id in chosen:
                left = [p for p in chosen if p != sub.subentry_id]
                if left:
                    item["data"] = {**item["data"], CONF_PARTITIONS: left}
                else:
                    item["data"] = {k: v for k, v in item["data"].items() if k != CONF_PARTITIONS}
    if sub.subentry_type in (SUBENTRY_SENSOR, SUBENTRY_SIREN):
        stored_all.pop(companion_id(entry, sub.subentry_id), None)  # its tamper contact goes with it
    save_stored(hass, entry, stored_all)
    connection.send_result(msg["id"], {"ok": True})


@websocket_api.websocket_command(
    {vol.Required("type"): "vigil_alarm/save_settings", vol.Required("data"): dict}
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
    first = {CONF_PARTITION_NAME, CONF_MODES, CONF_DEFAULT_ENTRY_DELAY, CONF_TRIGGER_TIME, CONF_CHIME_ENTITY,
             *(CONF_EXIT_DELAY.format(mode=m) for m in MODES)}  # the first partition: edited under Partitions
    data = {k: v for k, v in msg["data"].items() if k in {f["key"] for f in settings_schema()} | first}
    if CONF_MODES not in data:  # the settings tab does not send them: they stay as they are
        data.update({k: v for k, v in entry.data.items() if k in first})
    try:
        length = int(data.get(CONF_MIN_CODE_LENGTH, MIN_CODE_LENGTH_FLOOR))
    except (TypeError, ValueError):
        length = 0
    if not MIN_CODE_LENGTH_FLOOR <= length <= MIN_CODE_LENGTH_CEILING:
        connection.send_result(
            msg["id"],
            _failure(EditError({CONF_MIN_CODE_LENGTH: "code_length_range"}, {"min": MIN_CODE_LENGTH_FLOOR, "max": MIN_CODE_LENGTH_CEILING})),
        )
        return
    data[CONF_MIN_CODE_LENGTH] = length
    try:
        days = int(data.get(CONF_LOG_RETENTION_DAYS, DEFAULT_LOG_RETENTION_DAYS))
    except (TypeError, ValueError):
        days = 0
    if not LOG_RETENTION_FLOOR <= days <= LOG_RETENTION_CEILING:
        connection.send_result(
            msg["id"],
            _failure(EditError({CONF_LOG_RETENTION_DAYS: "log_retention_range"}, {"min": LOG_RETENTION_FLOOR, "max": LOG_RETENTION_CEILING})),
        )
        return
    data[CONF_LOG_RETENTION_DAYS] = days
    try:
        versions = int(data.get(CONF_BACKUP_VERSIONS, DEFAULT_BACKUP_VERSIONS))
    except (TypeError, ValueError):
        versions = 0
    if not BACKUP_VERSIONS_RANGE[0] <= versions <= BACKUP_VERSIONS_RANGE[1]:
        connection.send_result(
            msg["id"],
            _failure(EditError({CONF_BACKUP_VERSIONS: "backup_versions_range"}, {"min": BACKUP_VERSIONS_RANGE[0], "max": BACKUP_VERSIONS_RANGE[1]})),
        )
        return
    data[CONF_BACKUP_VERSIONS] = versions
    try:
        screen = int(data.get(CONF_SCREEN_OFF_SECONDS, DEFAULT_SCREEN_OFF_SECONDS))
    except (TypeError, ValueError):
        screen = 0
    if not SCREEN_OFF_RANGE[0] <= screen <= SCREEN_OFF_RANGE[1]:
        connection.send_result(
            msg["id"],
            _failure(EditError({CONF_SCREEN_OFF_SECONDS: "screen_off_range"}, {"min": SCREEN_OFF_RANGE[0], "max": SCREEN_OFF_RANGE[1]})),
        )
        return
    data[CONF_SCREEN_OFF_SECONDS] = screen
    try:
        wait = int(data.get(CONF_STARTUP_WAIT, DEFAULT_STARTUP_WAIT))
    except (TypeError, ValueError):
        wait = 0
    if not STARTUP_WAIT_RANGE[0] <= wait <= STARTUP_WAIT_RANGE[1]:
        connection.send_result(
            msg["id"],
            _failure(EditError({CONF_STARTUP_WAIT: "startup_wait_range"}, {"min": STARTUP_WAIT_RANGE[0], "max": STARTUP_WAIT_RANGE[1]})),
        )
        return
    data[CONF_STARTUP_WAIT] = wait
    for key, default in LOCK_DEFAULTS.items():
        low, high = LOCK_WAIT_RANGE if "wait" in key else LOCK_TRIES_RANGE
        try:
            value = int(data.get(key, entry.data.get(key, default)))
        except (TypeError, ValueError):
            value = low - 1
        if not low <= value <= high:
            connection.send_result(
                msg["id"],
                _failure(EditError({key: "lock_wait_range" if "wait" in key else "lock_tries_range"}, {"min": low, "max": high})),
            )
            return
        data[key] = value
    data[CONF_SCREEN_OFF_ON_ALARM] = bool(data.get(CONF_SCREEN_OFF_ON_ALARM, DEFAULT_SCREEN_OFF_ON_ALARM))
    for key, (low, high), default in (
        (CONF_ABORT_SECONDS, ABORT_SECONDS_RANGE, DEFAULT_ABORT_SECONDS),
        (CONF_CHIME_SECONDS, CHIME_SECONDS_RANGE, DEFAULT_CHIME_SECONDS),
        (CONF_PARTITION_RETURN_SECONDS, PARTITION_RETURN_RANGE, DEFAULT_PARTITION_RETURN_SECONDS),
    ):
        try:
            value = int(data.get(key, default))
        except (TypeError, ValueError):
            value = low - 1
        if not low <= value <= high:
            connection.send_result(msg["id"], _failure(EditError({key: "seconds_range"}, {"min": low, "max": high})))
            return
        data[key] = value
    chime_entity = str(data.get(CONF_CHIME_ENTITY) or "").strip()
    if chime_entity and chime_entity.split(".")[0] not in CHIME_DOMAINS:
        connection.send_result(msg["id"], _failure(EditError({CONF_CHIME_ENTITY: "chime_entity_domain"})))
        return
    if chime_entity:
        data[CONF_CHIME_ENTITY] = chime_entity
    else:
        data.pop(CONF_CHIME_ENTITY, None)
    name = str(data.get(CONF_PARTITION_NAME) or "").strip()
    if name:
        if any(s.title == name for s in items_of(entry).values() if s.subentry_type == SUBENTRY_PARTITION):
            connection.send_result(msg["id"], _failure(EditError({CONF_PARTITION_NAME: "name_in_use"})))
            return
        data[CONF_PARTITION_NAME] = name[:60]
    else:
        data.pop(CONF_PARTITION_NAME, None)
    for key, (low, high) in SELFTEST_RANGES.items():
        try:
            value = int(data.get(key, entry.data.get(key, DEFAULT_SELFTEST[key])))
        except (TypeError, ValueError):
            value = low - 1
        if not low <= value <= high:
            connection.send_result(
                msg["id"], _failure(EditError({key: "selftest_range"}, {"min": low, "max": high}))
            )
            return
        data[key] = value
    if data["selftest_window_start"] >= data["selftest_window_end"]:
        connection.send_result(msg["id"], _failure(EditError({"selftest_window_end": "selftest_window"})))
        return
    data[CONF_SELFTEST_AUTO] = bool(data.get(CONF_SELFTEST_AUTO, False))
    data[CONF_SELFTEST_HANDLERS] = bool(data.get(CONF_SELFTEST_HANDLERS, False))
    url = str(data.get(CONF_HEARTBEAT_URL) or "").strip()
    if url and not valid_url(url):
        connection.send_result(msg["id"], _failure(EditError({CONF_HEARTBEAT_URL: "heartbeat_url_invalid"})))
        return
    data[CONF_HEARTBEAT_URL] = url
    try:
        minutes = int(data.get(CONF_HEARTBEAT_INTERVAL, DEFAULT_HEARTBEAT_INTERVAL))
    except (TypeError, ValueError):
        minutes = 0
    if not HEARTBEAT_INTERVAL_RANGE[0] <= minutes <= HEARTBEAT_INTERVAL_RANGE[1]:
        connection.send_result(
            msg["id"],
            _failure(EditError({CONF_HEARTBEAT_INTERVAL: "heartbeat_range"}, {"min": HEARTBEAT_INTERVAL_RANGE[0], "max": HEARTBEAT_INTERVAL_RANGE[1]})),
        )
        return
    data[CONF_HEARTBEAT_INTERVAL] = minutes
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


# ------------------------------------------------- back-ups, export and import


def _backups(entry: ConfigEntry):
    manager = getattr(entry, "runtime_data", None)
    return None if manager is None else manager.backups


def _backup_failure(err: BackupError) -> dict[str, Any]:
    return {"ok": False, "errors": {"base": err.code}, "placeholders": err.placeholders}


@websocket_api.websocket_command({vol.Required("type"): "vigil_alarm/backups"})
@websocket_api.require_admin
@callback
def ws_backups(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    entry = _entry_for(hass)
    backups = _backups(entry) if entry else None
    if backups is None:
        _no_entry(connection, msg)
        return
    connection.send_result(msg["id"], {"versions": backups.listing(), "entry_version": ENTRY_VERSION})


@websocket_api.websocket_command(
    {vol.Required("type"): "vigil_alarm/backup_restore", vol.Required("version_id"): str, vol.Optional("preview", default=False): bool}
)
@websocket_api.require_admin
@callback
def ws_backup_restore(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    """Put a version back. With `preview` only say what would change."""
    entry = _entry_for(hass)
    backups = _backups(entry) if entry else None
    if entry is None or backups is None:
        _no_entry(connection, msg)
        return
    try:
        state = backups.state_of(msg["version_id"])
    except BackupError as err:
        connection.send_result(msg["id"], _backup_failure(err))
        return
    change = backups.change_for(state)
    if msg["preview"]:
        connection.send_result(msg["id"], {"ok": True, "change": change})
        return
    if not change["empty"]:
        mark_backup_reason(hass, entry, "restore")
        hass.config_entries.async_update_entry(entry, data=state["data"], options=state["options"])
    connection.send_result(msg["id"], {"ok": True, "change": change})


@websocket_api.websocket_command({vol.Required("type"): "vigil_alarm/export"})
@websocket_api.require_admin
@callback
def ws_export(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    entry = _entry_for(hass)
    if entry is None:
        _no_entry(connection, msg)
        return
    backups = _backups(entry)
    connection.send_result(msg["id"], export_payload(entry, _VERSION, backups.changed_at if backups else None))


@websocket_api.websocket_command(
    {vol.Required("type"): "vigil_alarm/import", vol.Required("payload"): dict, vol.Optional("preview", default=False): bool}
)
@websocket_api.require_admin
@callback
def ws_import(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    """Replace the configuration by an export file. With `preview` only say what would change.

    Applying it first keeps the present configuration as a version, so an import can be undone.
    """
    entry = _entry_for(hass)
    backups = _backups(entry) if entry else None
    if entry is None or backups is None:
        _no_entry(connection, msg)
        return
    try:
        state = read_backup_payload(msg["payload"])
    except BackupError as err:
        connection.send_result(msg["id"], _backup_failure(err))
        return
    change = backups.change_for(state)
    if not msg["preview"] and not change["empty"]:
        mark_backup_reason(hass, entry, "import")
        hass.config_entries.async_update_entry(entry, data=state["data"], options=state["options"])
    connection.send_result(msg["id"], {"ok": True, "change": change})


@websocket_api.websocket_command(
    {vol.Required("type"): "vigil_alarm/arm_check", vol.Required("mode"): str, vol.Optional("partition"): str}
)
@websocket_api.require_admin
@callback
def ws_arm_check(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    """Why can't I arm in this mode? What stops it, per sensor; nothing changes."""
    entry = _entry_for(hass)
    manager = getattr(entry, "runtime_data", None) if entry else None
    if manager is None:
        _no_entry(connection, msg)
        return
    part = manager.partitions.get(msg.get("partition") or PRIMARY_PARTITION)
    if part is None or msg["mode"] not in part.config.modes:
        connection.send_error(msg["id"], "unknown_mode", "Unknown mode")
        return
    connection.send_result(msg["id"], {"blockers": manager.arm_blockers(msg["mode"], partition=part.id)})


@callback
def async_register_commands(hass: HomeAssistant) -> None:
    for command in (ws_get, ws_about, ws_tablet, ws_discover, ws_discover_ignore, ws_new_sensors_dismiss, ws_alarm_memory_clear, ws_practice, ws_walktest, ws_discover_report, ws_readiness, ws_log, ws_log_export, ws_selftest, ws_heartbeat, ws_panel_unlock, ws_panel_clear_lock, ws_panel_key, ws_dashboard, ws_add_phone, ws_create_default_groups, ws_subscribe, ws_save, ws_save_many, ws_delete, ws_save_settings, ws_siren_preset, ws_backups, ws_backup_restore, ws_export, ws_import, ws_arm_check):
        websocket_api.async_register_command(hass, command)


