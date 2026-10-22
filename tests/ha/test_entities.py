from __future__ import annotations

import pytest
from homeassistant.core import Context
from homeassistant.exceptions import Unauthorized
from custom_components.vigil_alarm.errors import VigilError as ServiceValidationError

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
    assert hass.states.get("binary_sensor.front_door_bypassed").state == "off"
    assert hass.states.get("binary_sensor.tamper_bypassed") is not None
    assert hass.states.get("binary_sensor.smoke_bypassed") is None  # fire cannot be bypassed
    assert hass.states.get("binary_sensor.kitchen_gas_bypassed") is None  # neither can gas
    assert hass.states.async_entity_ids("switch") == []  # no bypass switches since 0.7.0
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
    assert hass.states.get("binary_sensor.living_pir_bypassed").state == "on"


async def test_the_bypass_indicator_is_read_only_and_follows_the_bypass(hass):
    from homeassistant.helpers import entity_registry as er

    await _house(hass)
    state = hass.states.get("binary_sensor.living_pir_bypassed")
    assert state.state == "off"
    assert er.async_get(hass).async_get("binary_sensor.living_pir_bypassed").entity_category == er.EntityCategory.DIAGNOSTIC
    await hass.services.async_call("vigil_alarm", "bypass", {"sensor": "binary_sensor.living_pir", "code": "1234"}, blocking=True)
    assert hass.states.get("binary_sensor.living_pir_bypassed").state == "on"


async def test_the_switches_of_an_earlier_version_are_removed(hass):
    from homeassistant.helpers import entity_registry as er
    from pytest_homeassistant_custom_component.common import MockConfigEntry  # noqa: F401

    entry = make_entry()
    entry.add_to_hass(hass)
    old = er.async_get(hass).async_get_or_create(
        "switch", "vigil_alarm", f"{entry.entry_id}_anything_bypass", config_entry=entry, suggested_object_id="front_door_bypass")
    assert old.entity_id == "switch.front_door_bypass"
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert er.async_get(hass).async_get("switch.front_door_bypass") is None


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
        "binary_sensor.front_door_bypassed",
    ):
        assert hass.states.get(entity_id) is not None, entity_id
    assert hass.states.get("binary_sensor.vigil_alarm_fire_alarm").attributes["friendly_name"].endswith("Brandalarm")
    assert hass.states.get("binary_sensor.front_door_bypassed").attributes["friendly_name"].endswith("Omzeild")
