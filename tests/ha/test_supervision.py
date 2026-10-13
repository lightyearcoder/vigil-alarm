from __future__ import annotations

import pytest
from homeassistant.exceptions import ServiceValidationError
from homeassistant.core import Context
from pytest_homeassistant_custom_component.common import async_mock_service

from .common import EVENTS, PANEL, sub
from .test_integration import _call, _tick
from .test_sirens import Mocks, _house, _record, siren

NOTIFY = sub("notification", "Anna", {"service": "mobile_app_anna", "categories": ["fault", "arming", "alarm"],
                                      "delay": 0, "priority": False}, "n1")
ESCALATION = sub("notification", "Escalation", {"service": "mobile_app_anna", "categories": ["alarm"],
                                                "delay": 60, "priority": False}, "n2")


def sensor_with_battery():
    return sub("zone", "Back door", {"entity_id": "binary_sensor.back", "cls": "intrusion", "type": "delayed",
                                     "sensor_groups": ["g_away"], "battery_entity": "sensor.back_battery"}, "back")


def problems(hass):
    return hass.states.get(PANEL).attributes["problems"]


def messages(m):
    return [c.data["message"] for c in m.notify]


async def test_sensor_battery_low_and_back_to_normal(hass):
    m = Mocks(hass)
    hass.states.async_set("binary_sensor.back", "off")
    hass.states.async_set("sensor.back_battery", "80")
    entry = await _house(hass, sensor_with_battery(), NOTIFY)
    seen = _record(hass, entry)
    hass.states.async_set("sensor.back_battery", "21")
    await hass.async_block_till_done()
    assert problems(hass) == [] and "battery_low" not in seen  # default limit is 20%
    hass.states.async_set("sensor.back_battery", "19")
    await hass.async_block_till_done()
    assert problems(hass) == [{"name": "Back door", "problem": "battery_low", "level": 19.0}]
    assert messages(m) == ["Battery low: Back door (19%)"]
    hass.states.async_set("sensor.back_battery", "18")  # still low: no second notice
    await hass.async_block_till_done()
    assert len(m.notify) == 1
    hass.states.async_set("sensor.back_battery", "100")
    await hass.async_block_till_done()
    assert problems(hass) == [] and messages(m)[-1] == "Battery ok again: Back door"


async def test_battery_limit_is_configurable(hass):
    m = Mocks(hass)
    hass.states.async_set("binary_sensor.back", "off")
    hass.states.async_set("sensor.back_battery", "80")
    await _house(hass, sensor_with_battery(), NOTIFY, battery_threshold=50)
    hass.states.async_set("sensor.back_battery", "45")
    await hass.async_block_till_done()
    assert len(problems(hass)) == 1


@pytest.mark.parametrize("value", ["unknown", "unavailable", "abc"])
async def test_unreadable_battery_value_changes_nothing(hass, value):
    m = Mocks(hass)
    hass.states.async_set("binary_sensor.back", "off")
    hass.states.async_set("sensor.back_battery", "10")
    await _house(hass, sensor_with_battery(), NOTIFY)
    assert len(problems(hass)) == 1  # low at startup, silently
    hass.states.async_set("sensor.back_battery", value)
    await hass.async_block_till_done()
    assert len(problems(hass)) == 1 and m.notify == []


async def test_problems_found_at_startup_are_listed_but_not_announced(hass):
    sent = async_mock_service(hass, "notify", "mobile_app_anna")  # before setup: startup is what we test
    hass.states.async_set("binary_sensor.back", "off")
    hass.states.async_set("sensor.back_battery", "5")
    await _house(hass, sensor_with_battery(), NOTIFY)
    assert problems(hass)[0]["problem"] == "battery_low"
    assert sent == []
    assert hass.states.get(EVENTS).state == "unknown"  # no event was published


async def test_battery_limit_is_inclusive(hass):
    Mocks(hass)
    hass.states.async_set("binary_sensor.back", "off")
    hass.states.async_set("sensor.back_battery", "80")
    await _house(hass, sensor_with_battery(), NOTIFY)
    hass.states.async_set("sensor.back_battery", "20")  # exactly the default limit
    await hass.async_block_till_done()
    assert len(problems(hass)) == 1


async def test_siren_availability(hass):
    m = Mocks(hass)
    hass.states.async_set("switch.siren", "off")
    await _house(hass, siren(), NOTIFY)
    hass.states.async_set("switch.siren", "unavailable")
    await hass.async_block_till_done()
    assert problems(hass) == [{"name": "Hall siren", "problem": "unavailable"}]
    assert messages(m) == ["Siren Hall siren is unavailable"]
    hass.states.async_set("switch.siren", "off")
    await hass.async_block_till_done()
    assert problems(hass) == [] and messages(m)[-1] == "Siren Hall siren is available again"


async def test_siren_power_mode(hass):
    m = Mocks(hass)
    hass.states.async_set("switch.siren", "off")
    hass.states.async_set("sensor.siren_power", "mains")
    await _house(hass, siren(power_entity="sensor.siren_power"), NOTIFY)
    hass.states.async_set("sensor.siren_power", "battery")
    await hass.async_block_till_done()
    assert problems(hass) == [{"name": "Hall siren", "problem": "on_battery"}]
    assert messages(m) == ["Siren Hall siren lost mains power and runs on its battery"]
    hass.states.async_set("sensor.siren_power", "mains")
    await hass.async_block_till_done()
    assert problems(hass) == [] and messages(m)[-1] == "Siren Hall siren is on mains power again"


async def test_siren_power_mode_with_another_battery_value(hass):
    Mocks(hass)
    hass.states.async_set("switch.siren", "off")
    hass.states.async_set("sensor.siren_power", "external")
    await _house(hass, siren(power_entity="sensor.siren_power", power_battery_value="Dry_Cell"))
    hass.states.async_set("sensor.siren_power", "dry_cell")  # case does not matter
    await hass.async_block_till_done()
    assert len(problems(hass)) == 1


async def test_silence_stops_the_siren_but_not_the_alarm(hass, hass_admin_user):
    m = Mocks(hass)
    entry = await _house(hass, siren(), NOTIFY)
    seen = _record(hass, entry)
    hass.states.async_set("binary_sensor.smoke", "on")
    await hass.async_block_till_done()
    assert len(m.on) == 1 and m.off == []
    with pytest.raises(ServiceValidationError):  # no code, no administrator
        await hass.services.async_call("vigil", "silence", {}, blocking=True)
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call("vigil", "silence", {"code": "0000"}, blocking=True)
    await hass.services.async_call("vigil", "silence", {"code": "5678"}, blocking=True)
    await hass.async_block_till_done()
    assert len(m.off) == 1 and hass.states.get(PANEL).state == "triggered"
    assert "alarm_silenced" in seen
    assert "Alarm silenced by Bob" in messages(m)
    # an administrator in the UI needs no code
    hass.states.async_set("binary_sensor.smoke", "off")
    await _call(hass, "alarm_disarm", code="1234")
    hass.states.async_set("binary_sensor.smoke", "on")
    await hass.async_block_till_done()
    await hass.services.async_call("vigil", "silence", {}, blocking=True, context=Context(user_id=hass_admin_user.id))
    await hass.async_block_till_done()
    assert len(m.on) == 2 and len(m.off) == 2  # second alarm sounded and was silenced by the administrator


async def test_a_new_higher_priority_cause_sounds_the_siren_again_after_silence(hass):
    m = Mocks(hass)
    await _house(hass, siren())
    await _call(hass, "alarm_arm_home", code="1234")
    hass.states.async_set("binary_sensor.tamper", "on")
    await hass.async_block_till_done()
    await hass.services.async_call("vigil", "silence", {"code": "1234"}, blocking=True)
    await hass.async_block_till_done()
    assert len(m.on) == 1 and len(m.off) == 1
    hass.states.async_set("binary_sensor.smoke", "on")  # fire beats tamper
    await hass.async_block_till_done()
    assert len(m.on) == 2


async def test_acknowledge_cancels_the_escalation(hass, freezer):
    m = Mocks(hass)
    await _house(hass, ESCALATION)
    hass.states.async_set("binary_sensor.smoke", "on")
    await hass.async_block_till_done()
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call("vigil", "acknowledge", {}, blocking=True)
    await hass.services.async_call("vigil", "acknowledge", {"code": "1234"}, blocking=True)
    await _tick(hass, freezer, 120)
    assert m.notify == []
    assert hass.states.get(EVENTS).attributes["event_type"] == "alarm_acknowledged"
    assert hass.states.get(EVENTS).attributes["user"] == "Anna"


