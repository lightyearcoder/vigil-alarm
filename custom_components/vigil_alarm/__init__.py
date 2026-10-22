"""Vigil Alarm: a modular alarm system for Home Assistant."""

from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ENTITY_ID, Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ConfigEntryError

from homeassistant.helpers import config_validation as cv, device_registry as dr, entity_registry as er
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.typing import ConfigType
from homeassistant.loader import async_get_integration

from .const import ATTR_SENSOR, DOMAIN, MODES, SERVICE_ACKNOWLEDGE, SERVICE_ARM, SERVICE_BYPASS, SERVICE_CHECK_CODE, SERVICE_DISARM, SERVICE_SILENCE, SERVICE_TEST_NOTIFICATION, SERVICE_TEST_SIREN, SERVICE_UNBYPASS, SERVICE_UNLOCK_PANEL, SERVICE_SELECT_PARTITION
from .errors import VigilError, async_prepare
from .manager import SIGNAL_UPDATE, VigilManager
from .migration import async_migrate_entry  # noqa: F401  (Home Assistant looks it up here)
from homeassistant.helpers.storage import Store

from .backups import STORAGE_VERSION as BACKUPS_STORAGE_VERSION, backups_store_key
from .eventlog import STORAGE_VERSION as EVENTLOG_STORAGE_VERSION
from .repairs import VigilRepairs
from .lockout import STORAGE_VERSION as LOCKOUT_STORAGE_VERSION
from .selftest import STORAGE_VERSION as SELFTEST_STORAGE_VERSION
from .panels import profile_object_id
from .panel import async_register_commands, async_register_panel, async_remove_panel
from .vigil_core import ConfigError

PLATFORMS = [
    Platform.ALARM_CONTROL_PANEL,
    Platform.BINARY_SENSOR,
    Platform.EVENT,
    Platform.SENSOR,
]

type VigilConfigEntry = ConfigEntry[VigilManager]

SERVICE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_SENSOR): cv.entity_id,
        vol.Optional("code"): cv.string,
        vol.Optional("source"): cv.string,
        vol.Optional("key"): cv.string,
    }
)

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Register the services (once, not per config entry)."""

    def _verify_key(call: ServiceCall) -> None:
        """A panel that has a key proves itself with it on every call (see `PanelRegistry.verify_key`)."""
        for entry in hass.config_entries.async_loaded_entries(DOMAIN):
            entry.runtime_data.panels.verify_key(call.data.get("source"), call.data.get("key"), call.context.user_id)

    async def _handle(call: ServiceCall, *, bypass: bool) -> None:
        _verify_key(call)
        # Calls from the UI carry a user; automations and scripts do not.
        sensor_entity = call.data[ATTR_SENSOR]
        for entry in hass.config_entries.async_loaded_entries(DOMAIN):
            manager: VigilManager = entry.runtime_data
            sensor_id = manager.sensor_id_for_entity(sensor_entity)
            if sensor_id:
                is_admin = await manager.async_is_admin(call.context)
                await manager.async_bypass(
                    sensor_id, call.data.get("code"), is_admin=is_admin, bypass=bypass,
                    source=call.data.get("source"), user_id=call.context.user_id,
                )
                return
        raise VigilError(translation_domain=DOMAIN, translation_key="unknown_sensor")

    async def bypass(call: ServiceCall) -> None:
        await _handle(call, bypass=True)

    async def unbypass(call: ServiceCall) -> None:
        await _handle(call, bypass=False)

    async def _control(call: ServiceCall, action: str) -> None:
        _verify_key(call)
        for entry in hass.config_entries.async_loaded_entries(DOMAIN):
            manager: VigilManager = entry.runtime_data
            is_admin = await manager.async_is_admin(call.context)
            await getattr(manager, action)(
                call.data.get("code"), is_admin=is_admin, source=call.data.get("source"),
                user_id=call.context.user_id,
            )

    async def silence(call: ServiceCall) -> None:
        await _control(call, "async_silence")

    async def acknowledge(call: ServiceCall) -> None:
        await _control(call, "async_acknowledge")

    code_schema = vol.Schema({vol.Optional("code"): cv.string, vol.Optional("source"): cv.string, vol.Optional("key"): cv.string})
    hass.services.async_register(DOMAIN, SERVICE_SILENCE, silence, schema=code_schema)
    hass.services.async_register(DOMAIN, SERVICE_ACKNOWLEDGE, acknowledge, schema=code_schema)

    async def arm(call: ServiceCall) -> None:
        _verify_key(call)
        for entry in hass.config_entries.async_loaded_entries(DOMAIN):
            await entry.runtime_data.async_arm(
                call.data["mode"], call.data.get("code"), call.data.get("source"), call.context.user_id,
                bypass_open=call.data.get("bypass_open", False), partition=call.data.get("partition"),
            )

    async def disarm(call: ServiceCall) -> None:
        _verify_key(call)
        for entry in hass.config_entries.async_loaded_entries(DOMAIN):
            await entry.runtime_data.async_disarm(call.data.get("code"), call.data.get("source"), call.context.user_id,
                partition=call.data.get("partition"),
            )

    # Arm and disarm with the name of the control point (a panel, a keypad) in the log.
    hass.services.async_register(
        DOMAIN, SERVICE_ARM, arm,
        schema=vol.Schema({
            vol.Required("mode"): vol.In(list(MODES)),
            vol.Optional("code"): cv.string,
            vol.Optional("source"): cv.string,
            vol.Optional("key"): cv.string,
            vol.Optional("bypass_open", default=False): cv.boolean,
            vol.Optional("partition"): cv.string,  # the id of a partition, or "all"; none: the first partition
        }),
    )
    hass.services.async_register(
        DOMAIN, SERVICE_DISARM, disarm,
        schema=code_schema.extend({vol.Optional("partition"): cv.string}),
    )

    async def check_code(call: ServiceCall) -> None:
        _verify_key(call)
        for entry in hass.config_entries.async_loaded_entries(DOMAIN):
            await entry.runtime_data.async_check_code(call.data.get("code"), call.data.get("source"), call.context.user_id)

    # Only checks a code and changes nothing: a panel uses it to unlock the list of sensors.
    hass.services.async_register(DOMAIN, SERVICE_CHECK_CODE, check_code, schema=code_schema)

    async def unlock_panel(call: ServiceCall) -> None:
        _verify_key(call)
        found = False
        for entry in hass.config_entries.async_loaded_entries(DOMAIN):
            source = await entry.runtime_data._operator(call.data["source"], call.context.user_id, "unlock_panel")
            if entry.runtime_data.panels.get(source):
                found = True
                await entry.runtime_data.panels.async_unlock_with_code(call.data["code"], source, call.data["scope"])
        if not found:
            raise VigilError(translation_domain=DOMAIN, translation_key="unknown_panel")

    # The panel sends a code; Vigil checks it. A Home Assistant action, but it only opens the
    # sensor list and the information pages for a short time and never disarms.
    hass.services.async_register(
        DOMAIN, SERVICE_UNLOCK_PANEL, unlock_panel,
        schema=vol.Schema({
            vol.Required("code"): cv.string,
            vol.Required("source"): cv.string,
            vol.Optional("key"): cv.string,
            # "sensors": the sensor list, a user code or the installer code; "info": the information pages, the installer code
            vol.Optional("scope", default="info"): vol.In(["sensors", "info"]),
        }),
    )

    async def select_partition(call: ServiceCall) -> None:
        _verify_key(call)
        found = False
        for entry in hass.config_entries.async_loaded_entries(DOMAIN):
            if entry.runtime_data.panels.get(call.data["source"]):
                found = True
                entry.runtime_data.panels.select(call.data["source"], call.data["partition"])
        if not found:
            raise VigilError(translation_domain=DOMAIN, translation_key="unknown_panel")

    # A panel that can switch between partitions says which one it shows. It changes what the panel gets to see
    # (its profile) and nothing else: arming and disarming still name the partition and need a code.
    hass.services.async_register(
        DOMAIN, SERVICE_SELECT_PARTITION, select_partition,
        schema=vol.Schema({vol.Required("source"): cv.string, vol.Required("partition"): cv.string, vol.Optional("key"): cv.string}),
    )

    async def test_notification(call: ServiceCall) -> None:
        sent = 0
        for entry in hass.config_entries.async_loaded_entries(DOMAIN):
            sent += await entry.runtime_data.notifier.async_test(call.data.get("channel"))
        if not sent:
            raise VigilError(translation_domain=DOMAIN, translation_key="no_channels")

    async def test_siren(call: ServiceCall) -> None:
        sounded = 0
        for entry in hass.config_entries.async_loaded_entries(DOMAIN):
            sounded += await entry.runtime_data.sirens.async_test(call.data.get("siren"), call.data["duration"])
        if not sounded:
            raise VigilError(translation_domain=DOMAIN, translation_key="no_sirens")
        for entry in hass.config_entries.async_loaded_entries(DOMAIN):
            entry.runtime_data.selftest.record_siren_test("manual")

    hass.services.async_register(
        DOMAIN,
        SERVICE_TEST_SIREN,
        test_siren,
        schema=vol.Schema(
            {
                vol.Optional("siren"): cv.string,
                vol.Optional("duration", default=3): vol.All(vol.Coerce(float), vol.Range(min=1, max=30)),
            }
        ),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_TEST_NOTIFICATION,
        test_notification,
        schema=vol.Schema({vol.Optional("channel"): cv.string}),
    )
    async def handler_report(call: ServiceCall) -> None:
        for entry in hass.config_entries.async_loaded_entries(DOMAIN):
            entry.runtime_data.handlers.report(dict(call.data))

    hass.services.async_register(
        DOMAIN,
        "handler_report",
        handler_report,
        schema=vol.Schema(
            {
                vol.Required("run_id"): cv.string,
                vol.Required("state"): vol.In(["started", "done", "failed"]),
                vol.Optional("handler"): cv.string,
                vol.Optional("automation"): cv.string,
                vol.Optional("event"): cv.string,
                vol.Optional("waits_for_user", default=False): cv.boolean,
                vol.Optional("max_duration"): vol.All(vol.Coerce(float), vol.Range(min=1)),
                vol.Optional("error"): cv.string,
            }
        ),
    )

    async def test_handlers(call: ServiceCall) -> None:
        found = False
        for entry in hass.config_entries.async_loaded_entries(DOMAIN):
            found = True
            entry.runtime_data.handlers.start_test(quiet=call.data["quiet"])
        if not found:
            raise VigilError(translation_domain=DOMAIN, translation_key="no_channels")

    hass.services.async_register(
        DOMAIN, "test_handlers", test_handlers, schema=vol.Schema({vol.Optional("quiet", default=True): cv.boolean})
    )

    async def clear_alarm_memory(call: ServiceCall) -> None:
        _verify_key(call)
        for entry in hass.config_entries.async_loaded_entries(DOMAIN):
            await entry.runtime_data.async_clear_alarm_memory(call.data.get("source"))

    hass.services.async_register(DOMAIN, "clear_alarm_memory", clear_alarm_memory, schema=vol.Schema({vol.Optional("source"): cv.string, vol.Optional("key"): cv.string}))
    hass.services.async_register(DOMAIN, SERVICE_BYPASS, bypass, schema=SERVICE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_UNBYPASS, unbypass, schema=SERVICE_SCHEMA)
    async_register_commands(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: VigilConfigEntry) -> bool:
    await async_prepare(hass)  # the texts of the errors, in the language of Home Assistant
    try:
        manager = VigilManager(hass, entry)
    except ConfigError as err:
        raise ConfigEntryError(
            translation_domain=DOMAIN,
            translation_key="invalid_config",
            translation_placeholders={"error": str(err)},
        ) from err
    await manager.async_setup()
    entry.runtime_data = manager
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    # The platforms are set up side by side: a panel profile can be written before the alarm entity exists.
    async_dispatcher_send(hass, SIGNAL_UPDATE.format(entry.entry_id))
    await async_register_panel(hass, (await async_get_integration(hass, DOMAIN)).version.string)
    _remove_orphans(hass, entry, manager)
    _align_profile_ids(hass, entry, manager)
    await manager.selftest.async_start()
    entry.async_on_unload(manager.selftest.stop)
    await manager.handlers.async_start()
    entry.async_on_unload(manager.handlers.stop)
    manager.heartbeat.start()
    entry.async_on_unload(manager.heartbeat.stop)
    entry.async_on_unload(VigilRepairs(hass, manager).start())
    # Changing the entry or its items rebuilds the engine from the new config.
    entry.async_on_unload(entry.add_update_listener(_reload))
    return True


def _remove_orphans(hass: HomeAssistant, entry: VigilConfigEntry, manager) -> None:
    """Remove the entities and devices of sensors that were deleted in the panel."""
    known = {s.subentry_id for s in manager.sensor_items()} | {p.subentry_id for p in manager.panels.items()}
    prefix = f"{entry.entry_id}_"
    ent_reg = er.async_get(hass)
    for ent in er.async_entries_for_config_entry(ent_reg, entry.entry_id):
        uid = ent.unique_id
        # Before 0.7.0 every sensor had a bypass switch; bypassing is no longer possible from a switch.
        if ent.domain == "switch" and uid.endswith("_bypass"):
            ent_reg.async_remove(ent.entity_id)
            continue
        # The alarm entities of a partition that was removed, and the "all" entity once there is one partition left.
        if ent.domain == "alarm_control_panel" and uid != entry.entry_id:
            wanted = {f"{entry.entry_id}_partition_{pid}" for pid in manager.partitions}
            if manager.multiple:
                wanted.add(f"{entry.entry_id}_all")
            if uid not in wanted:
                ent_reg.async_remove(ent.entity_id)
            continue
        if uid.startswith(prefix) and uid.count("_") >= 2:
            sid = uid[len(prefix):].rsplit("_", 1)[0]
            if sid not in known and (uid.endswith("_status") or uid.endswith("_bypassed") or uid.endswith("_profile")):
                ent_reg.async_remove(ent.entity_id)
    dev_reg = dr.async_get(hass)
    for dev in dr.async_entries_for_config_entry(dev_reg, entry.entry_id):
        for domain, ident in dev.identifiers:
            if domain == DOMAIN and ident.startswith(prefix) and ident[len(prefix):] not in known:
                dev_reg.async_remove_device(dev.id)


def _align_profile_ids(hass: HomeAssistant, entry: VigilConfigEntry, manager) -> None:
    """A profile sensor made by an earlier version (or before the panel id was changed) has an entity id that
    follows the name it had then; the firmware looks for the one that follows the panel id. Home Assistant never
    renames an entity by itself, so it is done here, once, if the right id is free."""
    ent_reg = er.async_get(hass)
    for panel in manager.panels.items():
        current = manager.panels.profile_entity_id(panel)
        wanted = f"sensor.{profile_object_id(panel.data['panel_id'])}"
        if not current or current == wanted:
            continue
        if ent_reg.async_get(wanted) is None:
            ent_reg.async_update_entity(current, new_entity_id=wanted)
        else:
            _LOGGER.warning("The profile sensor of panel %s is %s, but %s is taken by another entity; the panel "
                            "will not find its profile until that one is removed or renamed",
                            panel.data["panel_id"], current, wanted)


async def _reload(hass: HomeAssistant, entry: VigilConfigEntry) -> None:
    await entry.runtime_data.backups.async_changed()  # keep the configuration as it was
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: VigilConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        await entry.runtime_data.async_unload()
    return unloaded


async def async_remove_entry(hass: HomeAssistant, entry: VigilConfigEntry) -> None:
    """The panel stays through reloads (every panel save reloads the entry); it goes with the entry."""
    async_remove_panel(hass)
    await Store(hass, EVENTLOG_STORAGE_VERSION, f"{DOMAIN}.log.{entry.entry_id}").async_remove()
    await Store(hass, SELFTEST_STORAGE_VERSION, f"{DOMAIN}.selftest.{entry.entry_id}").async_remove()
    await Store(hass, LOCKOUT_STORAGE_VERSION, f"{DOMAIN}.lockout.{entry.entry_id}").async_remove()
    await Store(hass, 1, f"{DOMAIN}.tablets.{entry.entry_id}").async_remove()
    await Store(hass, BACKUPS_STORAGE_VERSION, backups_store_key(entry.entry_id)).async_remove()
    await Store(hass, 1, f"{DOMAIN}.newsensors.{entry.entry_id}").async_remove()
    await Store(hass, 1, f"{DOMAIN}.alarmmemory.{entry.entry_id}").async_remove()
    await Store(hass, 1, f"{DOMAIN}.handlers.{entry.entry_id}").async_remove()
