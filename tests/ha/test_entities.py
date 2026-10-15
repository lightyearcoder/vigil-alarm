from __future__ import annotations

import pytest
from homeassistant.core import Context
from homeassistant.exceptions import ServiceValidationError, Unauthorized

from .common import PANEL, make_entry, sub
from .test_integration import _call, _setup, _tick

WATER = sub("zone", "Kitchen water", {"entity_id": "binary_sensor.water", "cls": "water"}, "water")
GAS = sub("zone", "Kitchen gas", {"entity_id": "binary_sensor.gas", "cls": "gas", "gas_type": "natural_gas"}, "gas")


async def _house(hass):
    hass.states.async_set("binary_sensor.water", "off")
    hass.states.async_set("binary_sensor.gas", "off")
    return await _setup(hass, make_entry(extra_subentries=[WATER, GAS]))


async def test_sensor_devices_and_entities(hass):
    from homeassistant.helpers import device_registry as dr, entity_registry as er

    entry = await _house(hass)
    assert hass.states.get("sensor.front_door_status").state == "closed"
    assert hass.states.get("switch.front_door_bypass").state == "off"
    assert hass.states.get("switch.tamper_bypass") is not None
    assert hass.states.get("switch.smoke_bypass") is None  # fire cannot be bypassed
    assert hass.states.get("switch.kitchen_gas_bypass") is None  # neither can gas
    devices = dr.async_entries_for_config_entry(dr.async_get(hass), entry.entry_id)
    assert {d.name for d in devices} >= {"Vigil Alarm", "Front door", "Smoke", "Kitchen water"}
    reg = er.async_get(hass).async_get("sensor.front_door_status")
    assert reg.config_subentry_id is None  # items are not config subentries


async def test_sensor_status_follows_the_sensor_and_bypass(hass):
    await _house(hass)
    hass.states.async_set("binary_sensor.living_pir", "on")
    await hass.async_block_till_done()
    assert hass.states.get("sensor.living_pir_status").state == "open"
    hass.states.async_set("binary_sensor.living_pir", "unavailable")
    await hass.async_block_till_done()
    assert hass.states.get("sensor.living_pir_status").state == "unavailable"
    hass.states.async_set("binary_sensor.living_pir", "off")
    await hass.async_block_till_done()
    await hass.services.async_call("vigil_alarm", "bypass", {"sensor": "binary_sensor.living_pir", "code": "1234"}, blocking=True)
    assert hass.states.get("sensor.living_pir_status").state == "bypassed"
    assert hass.states.get("switch.living_pir_bypass").state == "on"


async def test_bypass_switch_needs_an_admin(hass, hass_admin_user, hass_read_only_user):
    await _house(hass)
    target = {"entity_id": "switch.living_pir_bypass"}
    with pytest.raises((Unauthorized, ServiceValidationError)):  # HA itself blocks read-only users
        await hass.services.async_call("switch", "turn_on", target, blocking=True, context=Context(user_id=hass_read_only_user.id))
    with pytest.raises(ServiceValidationError):  # automations carry no user either
        await hass.services.async_call("switch", "turn_on", target, blocking=True)
    await hass.services.async_call("switch", "turn_on", target, blocking=True, context=Context(user_id=hass_admin_user.id))
    assert hass.states.get("switch.living_pir_bypass").state == "on"
    await hass.services.async_call("switch", "turn_off", target, blocking=True, context=Context(user_id=hass_admin_user.id))
    assert hass.states.get("switch.living_pir_bypass").state == "off"
    # an administrator may bypass tamper from the UI
    await hass.services.async_call("switch", "turn_on", {"entity_id": "switch.tamper_bypass"}, blocking=True, context=Context(user_id=hass_admin_user.id))
    assert hass.states.get("switch.tamper_bypass").state == "on"


async def test_alarm_active_per_class(hass):
    await _house(hass)
    assert hass.states.get("binary_sensor.vigil_alarm_intrusion_alarm").state == "off"
    assert hass.states.get("binary_sensor.vigil_alarm_fire_alarm").state == "off"
    hass.states.async_set("binary_sensor.smoke", "on")
    await hass.async_block_till_done()
    assert hass.states.get("binary_sensor.vigil_alarm_fire_alarm").state == "on"
    assert hass.states.get("binary_sensor.vigil_alarm_intrusion_alarm").state == "off"
    assert hass.states.get(PANEL).attributes["cause"] == "fire"
    await _call(hass, "alarm_disarm", code="1234")
    assert hass.states.get("binary_sensor.vigil_alarm_fire_alarm").state == "off"


async def test_every_class_has_an_alarm_entity_even_without_a_sensor(hass):
    await _setup(hass)  # no gas or water sensor configured
    for name in ("intrusion", "fire", "gas", "tamper", "water"):
        state = hass.states.get(f"binary_sensor.vigil_alarm_{name}_alarm")
        assert state is not None and state.state == "off"


async def test_water_is_a_technical_alarm_that_leaves_the_alarm_state_alone(hass):
    await _house(hass)
    hass.states.async_set("binary_sensor.water", "on")
    await hass.async_block_till_done()
    water = hass.states.get("binary_sensor.vigil_alarm_water_alarm")
    assert water.state == "on" and water.attributes["sensors"] == ["Kitchen water"]
    assert hass.states.get(PANEL).state == "disarmed"
    hass.states.async_set("binary_sensor.water", "off")
    await hass.async_block_till_done()
    assert hass.states.get("binary_sensor.vigil_alarm_water_alarm").state == "off"


async def test_last_event_sensor(hass):
    await _house(hass)
    await _call(hass, "alarm_arm_home", code="1234")
    state = hass.states.get("sensor.vigil_alarm_last_event")
    assert state.state == "armed" and state.attributes["user"] == "Anna"


async def test_entity_ids_are_english_on_a_dutch_installation_but_the_names_are_dutch(hass):
    hass.config.language = "nl"
    await _setup(hass)
    for entity_id in (
        "binary_sensor.vigil_alarm_fire_alarm",
        "binary_sensor.vigil_alarm_water_alarm",
        "sensor.vigil_alarm_last_event",
        "event.vigil_alarm_alarm_events",
        "sensor.front_door_status",
        "switch.front_door_bypass",
    ):
        assert hass.states.get(entity_id) is not None, entity_id
    assert hass.states.get("binary_sensor.vigil_alarm_fire_alarm").attributes["friendly_name"].endswith("Brandalarm")
    assert hass.states.get("switch.front_door_bypass").attributes["friendly_name"].endswith("Omzeilen")
