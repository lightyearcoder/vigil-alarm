from __future__ import annotations

from datetime import timedelta

import pytest
from homeassistant.components.alarm_control_panel import DOMAIN as ACP
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import async_fire_time_changed

from custom_components.vigil_alarm.const import DOMAIN

from .common import EVENTS, PANEL, make_entry


async def _setup(hass: HomeAssistant, entry=None, closed=("front_door", "living_pir", "smoke", "tamper")):
    for name in closed:
        hass.states.async_set(f"binary_sensor.{name}", "off")
    entry = entry or make_entry()
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def _call(hass, service, **data):
    await hass.services.async_call(ACP, service, {"entity_id": PANEL, **data}, blocking=True)


async def _tick(hass, freezer, seconds):
    freezer.tick(timedelta(seconds=seconds))
    async_fire_time_changed(hass, dt_util.utcnow())
    await hass.async_block_till_done()


async def test_entity_starts_disarmed(hass):
    entry = await _setup(hass)
    assert entry.state is ConfigEntryState.LOADED
    state = hass.states.get(PANEL)
    assert state.state == "disarmed"
    assert state.attributes["code_arm_required"] is True
    assert state.attributes["code_format"] == "number"
    assert state.attributes["supported_features"] == 1 | 2 | 4


async def test_arm_away_with_exit_delay_then_door_triggers_after_entry_delay(hass, freezer):
    await _setup(hass)
    await _call(hass, "alarm_arm_away", code="1234")
    assert hass.states.get(PANEL).state == "arming"
    await _tick(hass, freezer, 60)
    state = hass.states.get(PANEL)
    assert state.state == "armed_away" and state.attributes["changed_by"] == "Anna"

    hass.states.async_set("binary_sensor.front_door", "on")
    await hass.async_block_till_done()
    assert hass.states.get(PANEL).state == "pending"
    await _tick(hass, freezer, 29)
    assert hass.states.get(PANEL).state == "pending"
    await _tick(hass, freezer, 1)
    state = hass.states.get(PANEL)
    assert state.state == "triggered" and state.attributes["cause_sensor"] == "Front door"


async def test_codes_are_checked(hass):
    await _setup(hass)
    with pytest.raises(ServiceValidationError):
        await _call(hass, "alarm_arm_home")  # code required
    with pytest.raises(ServiceValidationError):
        await _call(hass, "alarm_arm_home", code="0000")
    with pytest.raises(ServiceValidationError, match="may not arm"):
        await _call(hass, "alarm_arm_away", code="5678")  # Bob: home only
    await _call(hass, "alarm_arm_home", code="5678")
    assert hass.states.get(PANEL).state == "armed_home"
    with pytest.raises(ServiceValidationError):
        await _call(hass, "alarm_disarm", code="0000")
    await _call(hass, "alarm_disarm", code="5678")
    assert hass.states.get(PANEL).state == "disarmed"


async def test_code_not_needed_to_arm_when_not_required_but_always_to_disarm(hass):
    await _setup(hass, make_entry(code_arm_required=False))
    assert hass.states.get(PANEL).attributes["code_arm_required"] is False
    await _call(hass, "alarm_arm_home")
    assert hass.states.get(PANEL).state == "armed_home"
    with pytest.raises(ServiceValidationError):
        await _call(hass, "alarm_disarm")


async def test_no_users_means_no_codes(hass):
    await _setup(hass, make_entry(users=False))
    state = hass.states.get(PANEL)
    assert state.attributes["code_format"] is None and state.attributes["code_arm_required"] is False
    await _call(hass, "alarm_arm_home")
    await _call(hass, "alarm_disarm")
    assert hass.states.get(PANEL).state == "disarmed"


async def test_fire_sensor_triggers_even_when_disarmed_and_blocks_arming(hass):
    await _setup(hass)
    hass.states.async_set("binary_sensor.smoke", "on")
    await hass.async_block_till_done()
    state = hass.states.get(PANEL)
    assert state.state == "triggered" and state.attributes["cause"] == "fire"
    with pytest.raises(ServiceValidationError, match="Arming refused"):
        await _call(hass, "alarm_arm_home", code="1234")
    await _call(hass, "alarm_disarm", code="1234")
    assert hass.states.get(PANEL).state == "disarmed"


async def test_event_entity_publishes_core_events(hass):
    await _setup(hass)
    await _call(hass, "alarm_arm_home", code="1234")
    state = hass.states.get(EVENTS)
    assert state.attributes["event_type"] == "armed"
    assert state.attributes["user"] == "Anna" and state.attributes["mode"] == "home"


async def test_state_survives_a_reload_and_timers_resume(hass, freezer):
    entry = await _setup(hass)
    await _call(hass, "alarm_arm_away", code="1234")
    await _tick(hass, freezer, 60)
    hass.states.async_set("binary_sensor.front_door", "on")
    await hass.async_block_till_done()
    assert hass.states.get(PANEL).state == "pending"

    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get(PANEL).state == "pending"  # entry delay still running

    await _tick(hass, freezer, 30)
    assert hass.states.get(PANEL).state == "triggered"


async def test_timer_that_expired_while_stopped_fires_on_start(hass, freezer):
    entry = await _setup(hass)
    await _call(hass, "alarm_arm_away", code="1234")
    await _tick(hass, freezer, 60)
    hass.states.async_set("binary_sensor.front_door", "on")
    await hass.async_block_till_done()
    assert await hass.config_entries.async_unload(entry.entry_id)
    freezer.tick(timedelta(seconds=300))  # HA was down
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get(PANEL).state == "triggered"


async def test_bypass_service_rules(hass):
    await _setup(hass)
    data = {"sensor": "binary_sensor.living_pir"}
    with pytest.raises(ServiceValidationError):  # no code, no admin context
        await hass.services.async_call(DOMAIN, "bypass", data, blocking=True)
    await hass.services.async_call(DOMAIN, "bypass", {**data, "code": "1234"}, blocking=True)
    assert "Living PIR" in hass.states.get(PANEL).attributes["bypassed_sensors"]
    await hass.services.async_call(DOMAIN, "unbypass", {**data, "code": "1234"}, blocking=True)
    assert hass.states.get(PANEL).attributes["bypassed_sensors"] == []
    with pytest.raises(ServiceValidationError, match="tamper"):
        await hass.services.async_call(DOMAIN, "bypass", {"sensor": "binary_sensor.tamper", "code": "1234"}, blocking=True)
    with pytest.raises(ServiceValidationError, match="cannot be bypassed"):
        await hass.services.async_call(DOMAIN, "bypass", {"sensor": "binary_sensor.smoke", "code": "1234"}, blocking=True)


async def test_sensors_are_trusted_only_after_the_startup_grace_period(hass, freezer):
    from homeassistant.core import CoreState

    hass.set_state(CoreState.not_running)
    # At HA start the sensors are not there yet: no sensor states, so no false faults.
    entry = make_entry()
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get(PANEL).state == "disarmed"
    with pytest.raises(ServiceValidationError, match="starting up"):
        await _call(hass, "alarm_arm_home", code="1234")

    for name in ("front_door", "living_pir", "smoke", "tamper"):
        hass.states.async_set(f"binary_sensor.{name}", "off")
    await hass.async_start()
    await hass.async_block_till_done()
    await _tick(hass, freezer, 11)
    await _call(hass, "alarm_arm_home", code="1234")
    assert hass.states.get(PANEL).state == "armed_home"
    events = hass.states.get(EVENTS).attributes
    assert events["event_type"] == "armed"


async def test_unusable_saved_state_starts_disarmed_with_an_event(hass, hass_storage):
    entry = make_entry()
    entry.add_to_hass(hass)
    hass_storage[f"vigil_alarm.{entry.entry_id}"] = {"version": 1, "key": f"vigil_alarm.{entry.entry_id}", "data": {"version": 99}}
    for name in ("front_door", "living_pir", "smoke", "tamper"):
        hass.states.async_set(f"binary_sensor.{name}", "off")
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get(PANEL).state == "disarmed"
    assert hass.states.get(EVENTS).attributes["event_type"] == "state_restore_failed"


async def test_sensor_that_goes_unavailable_blocks_arming_for_intrusion_sensors(hass):
    await _setup(hass)
    hass.states.async_set("binary_sensor.living_pir", "unavailable")
    await hass.async_block_till_done()
    with pytest.raises(ServiceValidationError, match="sensor_unavailable.*Living PIR"):
        await _call(hass, "alarm_arm_away", code="1234")
    await _call(hass, "alarm_arm_home", code="1234")  # living PIR is not part of 'home'
    assert hass.states.get(PANEL).state == "armed_home"
