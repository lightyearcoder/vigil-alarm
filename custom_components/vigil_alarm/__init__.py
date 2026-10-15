"""Vigil Alarm: a modular alarm system for Home Assistant."""

from __future__ import annotations

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ENTITY_ID, Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ConfigEntryError, ServiceValidationError
from homeassistant.helpers import config_validation as cv, device_registry as dr, entity_registry as er
from homeassistant.helpers.typing import ConfigType
from homeassistant.loader import async_get_integration

from .const import ATTR_SENSOR, DOMAIN, SERVICE_ACKNOWLEDGE, SERVICE_ARM, SERVICE_BYPASS, SERVICE_CHECK_CODE, SERVICE_DISARM, SERVICE_SILENCE, SERVICE_TEST_NOTIFICATION, SERVICE_TEST_SIREN, SERVICE_UNBYPASS
from .manager import VigilManager
from .migration import async_migrate_entry  # noqa: F401  (Home Assistant looks it up here)
from .repairs import VigilRepairs
from .panel import async_register_commands, async_register_panel, async_remove_panel
from .vigil_core import ConfigError

PLATFORMS = [
    Platform.ALARM_CONTROL_PANEL,
    Platform.BINARY_SENSOR,
    Platform.EVENT,
    Platform.SENSOR,
    Platform.SWITCH,
]

type VigilConfigEntry = ConfigEntry[VigilManager]

SERVICE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_SENSOR): cv.entity_id,
        vol.Optional("code"): cv.string,
        vol.Optional("source"): cv.string,
    }
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Register the services (once, not per config entry)."""

    async def _handle(call: ServiceCall, *, bypass: bool) -> None:
        # Calls from the UI carry a user; automations and scripts do not.
        sensor_entity = call.data[ATTR_SENSOR]
        for entry in hass.config_entries.async_loaded_entries(DOMAIN):
            manager: VigilManager = entry.runtime_data
            sensor_id = manager.sensor_id_for_entity(sensor_entity)
            if sensor_id:
                is_admin = await manager.async_is_admin(call.context)
                await manager.async_bypass(
                    sensor_id, call.data.get("code"), is_admin=is_admin, bypass=bypass,
                    source=call.data.get("source"),
                )
                return
        raise ServiceValidationError(translation_domain=DOMAIN, translation_key="unknown_sensor")

    async def bypass(call: ServiceCall) -> None:
        await _handle(call, bypass=True)

    async def unbypass(call: ServiceCall) -> None:
        await _handle(call, bypass=False)

    async def _control(call: ServiceCall, action: str) -> None:
        for entry in hass.config_entries.async_loaded_entries(DOMAIN):
            manager: VigilManager = entry.runtime_data
            is_admin = await manager.async_is_admin(call.context)
            await getattr(manager, action)(
                call.data.get("code"), is_admin=is_admin, source=call.data.get("source")
            )

    async def silence(call: ServiceCall) -> None:
        await _control(call, "async_silence")

    async def acknowledge(call: ServiceCall) -> None:
        await _control(call, "async_acknowledge")

    code_schema = vol.Schema({vol.Optional("code"): cv.string, vol.Optional("source"): cv.string})
    hass.services.async_register(DOMAIN, SERVICE_SILENCE, silence, schema=code_schema)
    hass.services.async_register(DOMAIN, SERVICE_ACKNOWLEDGE, acknowledge, schema=code_schema)

    async def arm(call: ServiceCall) -> None:
        for entry in hass.config_entries.async_loaded_entries(DOMAIN):
            await entry.runtime_data.async_arm(call.data["mode"], call.data.get("code"), call.data.get("source"))

    async def disarm(call: ServiceCall) -> None:
        for entry in hass.config_entries.async_loaded_entries(DOMAIN):
            await entry.runtime_data.async_disarm(call.data.get("code"), call.data.get("source"))

    # Arm and disarm with the name of the control point (a panel, a keypad) in the log.
    hass.services.async_register(
        DOMAIN, SERVICE_ARM, arm,
        schema=vol.Schema({
            vol.Required("mode"): vol.In(["home", "away", "night"]),
            vol.Optional("code"): cv.string,
            vol.Optional("source"): cv.string,
        }),
    )
    hass.services.async_register(DOMAIN, SERVICE_DISARM, disarm, schema=code_schema)

    async def check_code(call: ServiceCall) -> None:
        for entry in hass.config_entries.async_loaded_entries(DOMAIN):
            await entry.runtime_data.async_check_code(call.data.get("code"), call.data.get("source"))

    # Only checks a code and changes nothing: a panel uses it to unlock the list of sensors.
    hass.services.async_register(DOMAIN, SERVICE_CHECK_CODE, check_code, schema=code_schema)

    async def test_notification(call: ServiceCall) -> None:
        sent = 0
        for entry in hass.config_entries.async_loaded_entries(DOMAIN):
            sent += await entry.runtime_data.notifier.async_test(call.data.get("channel"))
        if not sent:
            raise ServiceValidationError(translation_domain=DOMAIN, translation_key="no_channels")

    async def test_siren(call: ServiceCall) -> None:
        sounded = 0
        for entry in hass.config_entries.async_loaded_entries(DOMAIN):
            sounded += await entry.runtime_data.sirens.async_test(call.data.get("siren"), call.data["duration"])
        if not sounded:
            raise ServiceValidationError(translation_domain=DOMAIN, translation_key="no_sirens")

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
    hass.services.async_register(DOMAIN, SERVICE_BYPASS, bypass, schema=SERVICE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_UNBYPASS, unbypass, schema=SERVICE_SCHEMA)
    async_register_commands(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: VigilConfigEntry) -> bool:
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
    await async_register_panel(hass, (await async_get_integration(hass, DOMAIN)).version.string)
    _remove_orphans(hass, entry, manager)
    entry.async_on_unload(VigilRepairs(hass, manager).start())
    # Changing the entry or its items rebuilds the engine from the new config.
    entry.async_on_unload(entry.add_update_listener(_reload))
    return True


def _remove_orphans(hass: HomeAssistant, entry: VigilConfigEntry, manager) -> None:
    """Remove the entities and devices of sensors that were deleted in the panel."""
    known = {s.subentry_id for s in manager.sensor_items()}
    prefix = f"{entry.entry_id}_"
    ent_reg = er.async_get(hass)
    for ent in er.async_entries_for_config_entry(ent_reg, entry.entry_id):
        uid = ent.unique_id
        if uid.startswith(prefix) and uid.count("_") >= 2:
            sid = uid[len(prefix):].rsplit("_", 1)[0]
            if sid not in known and (uid.endswith("_status") or uid.endswith("_bypass")):
                ent_reg.async_remove(ent.entity_id)
    dev_reg = dr.async_get(hass)
    for dev in dr.async_entries_for_config_entry(dev_reg, entry.entry_id):
        for domain, ident in dev.identifiers:
            if domain == DOMAIN and ident.startswith(prefix) and ident[len(prefix):] not in known:
                dev_reg.async_remove_device(dev.id)


async def _reload(hass: HomeAssistant, entry: VigilConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: VigilConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        await entry.runtime_data.async_unload()
    return unloaded


async def async_remove_entry(hass: HomeAssistant, entry: VigilConfigEntry) -> None:
    """The panel stays through reloads (every panel save reloads the entry); it goes with the entry."""
    async_remove_panel(hass)
