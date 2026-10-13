"""The test package in docs/ must work, because the install guide tells people to use it."""

from __future__ import annotations

import pathlib
from datetime import timedelta

from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util
from homeassistant.util.yaml import load_yaml
from pytest_homeassistant_custom_component.common import async_fire_time_changed

from .common import PANEL, make_entry, sub
from .test_integration import _call

PACKAGE = pathlib.Path(__file__).parents[2] / "docs" / "vigil_test_package.yaml"


async def _settle(hass, freezer):
    """Template entities refresh a moment after their source changes."""
    freezer.tick(timedelta(seconds=2))
    async_fire_time_changed(hass, dt_util.utcnow())
    await hass.async_block_till_done()


async def test_package_entities_work_with_vigil(hass, freezer):
    package = load_yaml(str(PACKAGE))
    for domain, config in package.items():
        assert await async_setup_component(hass, domain, {domain: config}), domain
    await hass.async_block_till_done()
    for entity in ("binary_sensor.vigil_test_front_door", "binary_sensor.vigil_test_smoke",
                   "binary_sensor.vigil_test_water", "switch.vigil_test_siren",
                   "sensor.vigil_test_battery_level", "sensor.vigil_test_siren_power_mode", "light.vigil_test_lamp"):
        assert hass.states.get(entity) is not None, entity

    def sensor(sid, title, key, **data):
        return sub("zone", title, {"entity_id": f"binary_sensor.vigil_test_{key}", **data}, sid)

    entry = make_entry(users=False, extra_subentries=[
        sub("siren", "Test siren", {"control": "switch.vigil_test_siren", "causes": ["intrusion", "fire", "gas", "tamper", "fault"],
                                    "max_duration": 180, "repeat_every": 0,
                                    "battery_entity": "sensor.vigil_test_battery_level",
                                    "power_entity": "sensor.vigil_test_siren_power_mode"}, "siren"),
    ])
    entry.add_to_hass(hass)
    for name in ("front_door", "living_pir", "smoke", "tamper"):
        hass.states.async_set(f"binary_sensor.{name}", "off")
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    # the default test entry uses binary_sensor.smoke; drive the package siren through a real alarm
    hass.states.async_set("binary_sensor.smoke", "on")
    await hass.async_block_till_done()
    assert hass.states.get(PANEL).state == "triggered"
    await _settle(hass, freezer)
    assert hass.states.get("switch.vigil_test_siren").state == "on"
    await _call(hass, "alarm_disarm")
    await _settle(hass, freezer)
    assert hass.states.get("switch.vigil_test_siren").state == "off"


async def test_the_virtual_lamp_can_be_switched(hass, freezer):
    package = load_yaml(str(PACKAGE))
    for domain, config in package.items():
        assert await async_setup_component(hass, domain, {domain: config}), domain
    await hass.async_block_till_done()
    assert hass.states.get("light.vigil_test_lamp").state == "off"
    await hass.services.async_call("light", "turn_on", {"entity_id": "light.vigil_test_lamp"}, blocking=True)
    await _settle(hass, freezer)
    assert hass.states.get("light.vigil_test_lamp").state == "on"
    await hass.services.async_call("light", "turn_off", {"entity_id": "light.vigil_test_lamp"}, blocking=True)
    await _settle(hass, freezer)
    assert hass.states.get("light.vigil_test_lamp").state == "off"
