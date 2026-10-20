"""What the whole installation does when something goes wrong: a restart in the middle of a delay or an alarm, a
restart that took longer than the delay, sensors that disappear, flap or report twice, commands that arrive twice.
These are the scenarios of docs/failure-behaviour.md; each test is one line of that table."""

from __future__ import annotations

from datetime import timedelta

import pytest
from homeassistant.exceptions import ServiceValidationError

from .common import EVENTS, PANEL, make_entry
from .test_integration import _call, _setup, _tick


def _state(hass):
    return hass.states.get(PANEL)


async def _reload(hass, entry):
    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()


async def _down_for(hass, freezer, entry, seconds):
    """Home Assistant is stopped for a while (power cut, update, crash) and then starts again."""
    assert await hass.config_entries.async_unload(entry.entry_id)
    freezer.tick(timedelta(seconds=seconds))
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


async def _armed_away(hass, freezer, **kwargs):
    entry = await _setup(hass, **kwargs)
    await _call(hass, "alarm_arm_away", code="1234")
    await _tick(hass, freezer, 60)
    assert _state(hass).state == "armed_away"
    return entry


# --- a restart in the middle of things ------------------------------------------------------------------------


async def test_a_restart_during_the_exit_delay_does_not_restart_the_delay(hass, freezer):
    entry = await _setup(hass)
    await _call(hass, "alarm_arm_away", code="1234")
    await _tick(hass, freezer, 20)
    await _reload(hass, entry)
    assert _state(hass).state == "arming"
    await _tick(hass, freezer, 39)
    assert _state(hass).state == "arming"
    await _tick(hass, freezer, 1)  # 60 s after the command, not 80
    assert _state(hass).state == "armed_away" and _state(hass).attributes["changed_by"] == "Anna"


async def test_an_exit_delay_that_ended_while_home_assistant_was_down_arms_on_start(hass, freezer):
    entry = await _setup(hass)
    await _call(hass, "alarm_arm_away", code="1234")
    await _down_for(hass, freezer, entry, 300)
    assert _state(hass).state == "armed_away"


async def test_a_restart_while_armed_keeps_it_armed(hass, freezer):
    entry = await _armed_away(hass, freezer)
    await _reload(hass, entry)
    state = _state(hass)
    assert state.state == "armed_away" and state.attributes["changed_by"] == "Anna"
    hass.states.async_set("binary_sensor.front_door", "on")  # and it still watches
    await hass.async_block_till_done()
    assert _state(hass).state == "pending"


async def test_a_door_that_was_opened_while_home_assistant_was_down_is_not_missed(hass, freezer):
    """The sensor is open when Vigil comes back: the alarm sees it as soon as the sensors are trusted again."""
    entry = await _armed_away(hass, freezer)
    assert await hass.config_entries.async_unload(entry.entry_id)
    hass.states.async_set("binary_sensor.front_door", "on")
    freezer.tick(timedelta(seconds=5))
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert _state(hass).state == "pending"  # the entry delay starts when Vigil sees it


async def test_a_restart_during_the_alarm_keeps_the_alarm_and_the_code_still_disarms(hass, freezer):
    entry = await _armed_away(hass, freezer)
    hass.states.async_set("binary_sensor.living_pir", "on")
    await hass.async_block_till_done()
    assert _state(hass).state == "triggered"
    await _reload(hass, entry)
    state = _state(hass)
    assert state.state == "triggered" and state.attributes["cause_sensor"] == "Living PIR"
    with pytest.raises(ServiceValidationError):
        await _call(hass, "alarm_disarm", code="0000")
    assert _state(hass).state == "triggered"
    await _call(hass, "alarm_disarm", code="1234")
    assert _state(hass).state == "disarmed"


async def test_several_restarts_in_a_row_in_the_entry_delay_neither_restart_nor_repeat_it(hass, freezer):
    entry = await _armed_away(hass, freezer)
    hass.states.async_set("binary_sensor.front_door", "on")
    await hass.async_block_till_done()
    await _tick(hass, freezer, 10)
    for _ in range(3):
        await _reload(hass, entry)
        assert _state(hass).state == "pending"
    await _tick(hass, freezer, 19)
    assert _state(hass).state == "pending"
    await _tick(hass, freezer, 1)  # 30 s after the door, however often it restarted
    assert _state(hass).state == "triggered"


async def test_a_disarm_after_a_restart_in_the_entry_delay_stops_it(hass, freezer):
    entry = await _armed_away(hass, freezer)
    hass.states.async_set("binary_sensor.front_door", "on")
    await hass.async_block_till_done()
    await _reload(hass, entry)
    await _call(hass, "alarm_disarm", code="1234")
    await _tick(hass, freezer, 120)
    assert _state(hass).state == "disarmed"


# --- sensors that disappear, flap or speak twice ------------------------------------------------------------------


async def test_a_sensor_that_drops_out_while_armed_is_reported_and_does_not_sound_the_alarm(hass, freezer):
    await _armed_away(hass, freezer)
    hass.states.async_set("binary_sensor.living_pir", "unavailable")
    await hass.async_block_till_done()
    assert _state(hass).state == "armed_away"
    assert hass.states.get(EVENTS).attributes["event_type"] == "supervision_lost"
    hass.states.async_set("binary_sensor.living_pir", "off")
    await hass.async_block_till_done()
    assert _state(hass).state == "armed_away"
    assert hass.states.get(EVENTS).attributes["event_type"] == "supervision_restored"


async def test_a_sensor_that_reports_the_same_state_twice_does_not_restart_the_entry_delay(hass, freezer):
    await _armed_away(hass, freezer)
    hass.states.async_set("binary_sensor.front_door", "on")
    await hass.async_block_till_done()
    await _tick(hass, freezer, 10)
    hass.states.async_set("binary_sensor.front_door", "on", {"battery": 50})  # same state, new attribute
    hass.states.async_set("binary_sensor.front_door", "on", {"battery": 49})
    await hass.async_block_till_done()
    await _tick(hass, freezer, 19)
    assert _state(hass).state == "pending"
    await _tick(hass, freezer, 1)
    assert _state(hass).state == "triggered"


async def test_a_door_that_closes_again_in_the_entry_delay_still_ends_in_an_alarm(hass, freezer):
    await _armed_away(hass, freezer)
    hass.states.async_set("binary_sensor.front_door", "on")
    await hass.async_block_till_done()
    await _tick(hass, freezer, 5)
    hass.states.async_set("binary_sensor.front_door", "off")
    await hass.async_block_till_done()
    assert _state(hass).state == "pending"
    await _tick(hass, freezer, 25)
    assert _state(hass).state == "triggered"


async def test_a_second_sensor_during_the_alarm_does_not_start_a_second_alarm(hass, freezer):
    await _armed_away(hass, freezer)
    hass.states.async_set("binary_sensor.living_pir", "on")
    await hass.async_block_till_done()
    assert _state(hass).state == "triggered"
    started = _state(hass).last_changed
    hass.states.async_set("binary_sensor.front_door", "on")
    await hass.async_block_till_done()
    await _tick(hass, freezer, 60)
    assert _state(hass).state == "triggered" and _state(hass).last_changed == started


async def test_smoke_during_an_intrusion_alarm_is_not_lost(hass, freezer):
    await _armed_away(hass, freezer)
    hass.states.async_set("binary_sensor.living_pir", "on")
    await hass.async_block_till_done()
    hass.states.async_set("binary_sensor.smoke", "on")
    await hass.async_block_till_done()
    assert _state(hass).state == "triggered"
    assert "fire" in str(_state(hass).attributes.get("cause"))


# --- commands that arrive twice or at the wrong moment -------------------------------------------------------------


async def test_the_same_arm_command_twice_during_the_exit_delay_does_not_extend_it(hass, freezer):
    await _setup(hass)
    await _call(hass, "alarm_arm_away", code="1234")
    await _tick(hass, freezer, 30)
    try:
        await _call(hass, "alarm_arm_away", code="1234")
    except ServiceValidationError:
        pass  # refusing the second command is as good as ignoring it
    await _tick(hass, freezer, 30)
    assert _state(hass).state == "armed_away"


async def test_disarming_twice_is_harmless(hass, freezer):
    await _armed_away(hass, freezer)
    await _call(hass, "alarm_disarm", code="1234")
    try:
        await _call(hass, "alarm_disarm", code="1234")
    except ServiceValidationError:
        pass
    assert _state(hass).state == "disarmed"


async def test_a_disarm_during_the_exit_delay_cancels_it(hass, freezer):
    await _setup(hass)
    await _call(hass, "alarm_arm_away", code="1234")
    await _tick(hass, freezer, 10)
    await _call(hass, "alarm_disarm", code="1234")
    await _tick(hass, freezer, 300)
    assert _state(hass).state == "disarmed"


# --- the alarm ends by itself -------------------------------------------------------------------------------------


async def test_an_alarm_that_ran_out_while_home_assistant_was_down_has_ended_on_start(hass, freezer):
    entry = await _armed_away(hass, freezer, entry=make_entry(trigger_time=120))
    hass.states.async_set("binary_sensor.living_pir", "on")
    await hass.async_block_till_done()
    assert _state(hass).state == "triggered"
    await _down_for(hass, freezer, entry, 3600)
    assert _state(hass).state == "armed_away"  # the siren time is over: armed again, not disarmed


# --- the rest of the installation fails as well ---------------------------------------------------------------------


async def test_an_alarm_still_sounds_and_can_be_disarmed_when_the_phone_and_the_siren_both_fail(hass, freezer):
    from homeassistant.exceptions import HomeAssistantError
    from pytest_homeassistant_custom_component.common import async_mock_service

    from .test_notifications import channel
    from .test_sirens import siren

    def broken(call):
        raise HomeAssistantError("offline")

    entry = await _setup(hass, make_entry(extra_subentries=[channel(categories=("alarm",)), siren()]))
    hass.services.async_register("notify", "mobile_app_anna", broken)
    hass.services.async_register("switch", "turn_on", broken)
    async_mock_service(hass, "switch", "turn_off")
    await _call(hass, "alarm_arm_away", code="1234")
    await _tick(hass, freezer, 60)
    hass.states.async_set("binary_sensor.living_pir", "on")
    await hass.async_block_till_done()
    assert _state(hass).state == "triggered"  # nothing that failed changed the alarm itself
    await _call(hass, "alarm_disarm", code="1234")
    assert _state(hass).state == "disarmed"
    assert entry.state.name == "LOADED"


# --- timing and several things at once ---------------------------------------------------------------------------


def _types(entry):
    return [e.get("event") for e in reversed(entry.runtime_data.eventlog.recent(500))]


async def test_a_restart_on_the_very_second_the_entry_delay_ends_still_ends_in_an_alarm(hass, freezer):
    entry = await _armed_away(hass, freezer)
    hass.states.async_set("binary_sensor.front_door", "on")
    await hass.async_block_till_done()
    freezer.tick(timedelta(seconds=30))  # the delay is over, but the timer has not been handled yet
    await _reload(hass, entry)
    assert _state(hass).state == "triggered"
    assert _types(entry).count("triggered") == 1


async def test_stopping_one_second_before_the_end_of_the_entry_delay_and_starting_one_second_after(hass, freezer):
    entry = await _armed_away(hass, freezer)
    hass.states.async_set("binary_sensor.front_door", "on")
    await hass.async_block_till_done()
    await _tick(hass, freezer, 29)
    await _down_for(hass, freezer, entry, 2)
    assert _state(hass).state == "triggered"


async def test_two_sensors_at_the_same_moment_make_one_alarm_from_the_one_that_acts_first(hass, freezer):
    entry = await _armed_away(hass, freezer)
    hass.states.async_set("binary_sensor.front_door", "on")  # an entry delay ...
    hass.states.async_set("binary_sensor.living_pir", "on")  # ... and an instant sensor in the same moment
    await hass.async_block_till_done()
    state = _state(hass)
    assert state.state == "triggered" and state.attributes["cause_sensor"] == "Living PIR"  # no waiting for the delay
    await _tick(hass, freezer, 60)
    assert _state(hass).state == "triggered"
    assert _types(entry).count("triggered") == 1


async def test_a_change_of_the_settings_during_the_entry_delay_does_not_move_the_end_of_it(hass, freezer):
    entry = await _armed_away(hass, freezer)
    hass.states.async_set("binary_sensor.front_door", "on")
    await hass.async_block_till_done()
    await _tick(hass, freezer, 10)
    hass.config_entries.async_update_entry(entry, data={**entry.data, "default_entry_delay": 120, "trigger_time": 300})
    await hass.async_block_till_done()
    assert _state(hass).state == "pending"
    await _tick(hass, freezer, 19)
    assert _state(hass).state == "pending"
    await _tick(hass, freezer, 1)  # 30 s after the door: the delay that was running keeps its end
    assert _state(hass).state == "triggered"


@pytest.mark.parametrize("junk", [
    {"version": 99},
    {"partitions": {"main": {"version": 1, "state": "triggered"}}},  # a state without the rest of it
    {"partitions": {"main": []}},
    {"partitions": {"main": {"version": 1, "state": "nonsense", "cause": 7}}},
])
async def test_an_unusable_saved_state_never_comes_back_armed_or_triggered(hass, hass_storage, junk):
    """Whatever is wrong with the saved state, the alarm starts disarmed, and says so when it had to give up."""
    entry = make_entry()
    entry.add_to_hass(hass)
    hass_storage[f"vigil_alarm.{entry.entry_id}"] = {"version": 1, "key": f"vigil_alarm.{entry.entry_id}", "data": junk}
    for name in ("front_door", "living_pir", "smoke", "tamper"):
        hass.states.async_set(f"binary_sensor.{name}", "off")
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert _state(hass).state == "disarmed"
