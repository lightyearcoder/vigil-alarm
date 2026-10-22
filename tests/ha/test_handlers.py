"""Release 0.7.0: do the automations that react to the alarm still run? (handler_report, the quiet test, repairs)"""

from __future__ import annotations

import asyncio
import pathlib
import shutil
from datetime import timedelta

import pytest
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import issue_registry as ir
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import async_fire_time_changed, async_mock_service

from custom_components.vigil_alarm.const import DOMAIN
from custom_components.vigil_alarm.handlers import START_TIMEOUT

from .common import EVENTS, PANEL, make_entry
from .test_integration import _call, _setup

BLUEPRINTS = pathlib.Path(__file__).parents[2] / "blueprints" / "automation" / "vigil_alarm"


async def _pump(hass, turns=40, settle=True):
    for _ in range(turns):
        await asyncio.sleep(0)
    if settle:  # not while lights flash: that loop never lets Home Assistant come to rest
        await hass.async_block_till_done()


async def _tick(hass, freezer, seconds, settle=True):
    freezer.tick(timedelta(seconds=seconds))
    async_fire_time_changed(hass, dt_util.utcnow())
    await _pump(hass, settle=settle)


async def _blueprints(hass, *specs):
    """Blueprint automations: (file, inputs, id); they are called automation.handler_<id>."""
    target = pathlib.Path(hass.config.path("blueprints/automation/vigil_alarm"))
    target.mkdir(parents=True, exist_ok=True)
    config = []
    for name, inputs, auto_id in specs:
        shutil.copy(BLUEPRINTS / name, target / name)
        config.append({"id": auto_id, "alias": f"Handler {auto_id}", "use_blueprint": {"path": f"vigil_alarm/{name}", "input": inputs}})
    assert await async_setup_component(hass, "automation", {"automation": config})
    await _pump(hass)


async def _house(hass):
    entry = await _setup(hass, make_entry())
    entry.runtime_data.selftest.stop()  # its daily check would start a test of its own while time passes
    return entry.runtime_data


def _kinds(manager):
    return [e["event"] for e in manager.eventlog.entries]


async def test_a_run_that_reports_started_and_done_is_fine(hass, freezer):
    manager = await _house(hass)
    await hass.services.async_call(DOMAIN, "handler_report", {
        "run_id": "r1", "state": "started", "handler": "Lights", "automation": "automation.lights"}, blocking=True)
    assert len(manager.handlers.runs) == 1
    await hass.services.async_call(DOMAIN, "handler_report", {"run_id": "r1", "state": "done"}, blocking=True)
    assert manager.handlers.runs == {} and manager.handlers.problems == {}


async def test_a_run_that_ends_without_done_is_stalled(hass, freezer):
    manager = await _house(hass)
    hass.states.async_set("automation.lights", "on", {"current": 1, "mode": "single", "friendly_name": "Lights"})
    await hass.services.async_call(DOMAIN, "handler_report", {
        "run_id": "r1", "state": "started", "handler": "Lights", "automation": "automation.lights"}, blocking=True)
    hass.states.async_set("automation.lights", "on", {"current": 1, "mode": "single", "friendly_name": "Lights"})
    await _pump(hass)
    assert manager.handlers.problems == {}  # still running: never a fault, however long it takes
    await _tick(hass, freezer, 7200)
    assert manager.handlers.problems == {}
    hass.states.async_set("automation.lights", "on", {"current": 0, "mode": "single", "friendly_name": "Lights"})
    await _pump(hass)
    assert list(manager.handlers.problems) == ["stalled:automation.lights"]
    assert "handler_stalled" in _kinds(manager)
    issue = ir.async_get(hass).async_get_issue(DOMAIN, f"{manager.entry.entry_id}_handler_stalled:automation.lights")
    assert issue is not None and issue.translation_key == "handler_stalled"
    findings = [f["code"] for f in manager.handlers.findings()]
    assert findings == ["handler_stalled"]
    # the next run that finishes clears it
    await hass.services.async_call(DOMAIN, "handler_report", {
        "run_id": "r2", "state": "started", "handler": "Lights", "automation": "automation.lights"}, blocking=True)
    await hass.services.async_call(DOMAIN, "handler_report", {"run_id": "r2", "state": "done", "automation": "automation.lights"}, blocking=True)
    assert manager.handlers.problems == {}
    assert ir.async_get(hass).async_get_issue(DOMAIN, f"{manager.entry.entry_id}_handler_stalled:automation.lights") is None


async def test_a_handler_that_says_failed_is_stalled_with_the_reason(hass):
    manager = await _house(hass)
    await hass.services.async_call(DOMAIN, "handler_report", {
        "run_id": "r1", "state": "started", "handler": "Speech", "automation": "automation.speech"}, blocking=True)
    await hass.services.async_call(DOMAIN, "handler_report", {"run_id": "r1", "state": "failed", "error": "no speaker"}, blocking=True)
    assert manager.handlers.problems["stalled:automation.speech"]["detail"] == "no speaker"


async def test_a_waiting_handler_may_wait_but_one_with_a_limit_is_told_once(hass, freezer):
    manager = await _house(hass)
    hass.states.async_set("automation.wait", "on", {"current": 1, "mode": "single"})
    await hass.services.async_call(DOMAIN, "handler_report", {
        "run_id": "w1", "state": "started", "automation": "automation.wait", "waits_for_user": True}, blocking=True)
    await _tick(hass, freezer, 86400)
    assert manager.handlers.problems == {}
    await hass.services.async_call(DOMAIN, "handler_report", {
        "run_id": "w2", "state": "started", "automation": "automation.wait", "max_duration": 120}, blocking=True)
    await _tick(hass, freezer, 130)
    await _tick(hass, freezer, 400)
    assert _kinds(manager).count("handler_slow") == 1 and manager.handlers.problems == {}


async def test_a_run_of_an_automation_vigil_cannot_see_ends_after_a_time_limit(hass, freezer):
    manager = await _house(hass)
    await hass.services.async_call(DOMAIN, "handler_report", {
        "run_id": "u1", "state": "started", "handler": "Mystery"}, blocking=True)
    await _tick(hass, freezer, 700)
    assert list(manager.handlers.problems) == ["stalled:Mystery"]


async def test_a_restart_mode_run_that_is_replaced_is_not_a_fault(hass):
    manager = await _house(hass)
    hass.states.async_set("automation.flash", "on", {"current": 1, "mode": "restart"})
    for run in ("a", "b"):
        await hass.services.async_call(DOMAIN, "handler_report", {
            "run_id": run, "state": "started", "automation": "automation.flash"}, blocking=True)
    assert list(manager.handlers.runs) == ["b"]
    hass.states.async_set("automation.flash", "on", {"current": 1, "mode": "restart", "x": 1})
    await _pump(hass)
    assert manager.handlers.problems == {}


async def test_the_quiet_test_only_makes_the_blueprints_report(hass, freezer):
    manager = await _house(hass)
    await _blueprints(
        hass,
        ("flash_lights_on_alarm.yaml", {"events": EVENTS, "lights": ["light.hall"]}, "flash"),
        ("announce_with_speech.yaml", {"partitions": [PANEL], "events": EVENTS, "tts": "tts.home", "speakers": ["media_player.kitchen"]}, "speech"),
    )
    on = async_mock_service(hass, "light", "turn_on")
    async_mock_service(hass, "light", "turn_off")
    async_mock_service(hass, "scene", "create")
    async_mock_service(hass, "scene", "turn_on")
    async_mock_service(hass, "scene", "delete")
    spoken = async_mock_service(hass, "tts", "speak")
    manager.handlers.known.clear()
    assert set(manager.handlers.handler_automations()) == {"automation.handler_flash", "automation.handler_speech"}
    manager.handlers.start_test(quiet=True)
    await _pump(hass)
    assert on == [] and spoken == []  # nothing flashed, nothing said
    assert manager.handlers.last_test is not None
    assert set(manager.handlers.last_test["result"].values()) == {"ok"} and len(manager.handlers.last_test["result"]) == 2
    assert manager.handlers.problems == {} and not manager.handlers.testing
    assert "handler_test" in _kinds(manager) and manager.last_event is None  # routine: not "the last event"


async def test_the_test_with_the_real_actions_runs_in_practice_mode(hass, freezer):
    manager = await _house(hass)
    await _blueprints(
        hass,
        ("flash_lights_on_alarm.yaml", {"events": EVENTS, "lights": ["light.hall"], "interval": 1}, "flash"),
        ("announce_with_speech.yaml", {"partitions": [PANEL], "events": EVENTS, "tts": "tts.home", "speakers": ["media_player.kitchen"]}, "speech"),
    )
    on = async_mock_service(hass, "light", "turn_on")
    async_mock_service(hass, "light", "turn_off")
    async_mock_service(hass, "scene", "create")
    async_mock_service(hass, "scene", "turn_on")
    async_mock_service(hass, "scene", "delete")
    spoken = async_mock_service(hass, "tts", "speak")
    await _call(hass, "alarm_arm_home", code="1234")
    await _pump(hass, settle=False)
    with pytest.raises(HomeAssistantError):
        manager.handlers.start_test(quiet=False)  # armed: not now
    await _call(hass, "alarm_disarm", code="1234")
    await _pump(hass, settle=False)
    spoken.clear()  # arming and disarming were announced, that is not the test
    on.clear()
    manager.handlers.start_test(quiet=False)
    assert manager.practice.active
    for _ in range(8):
        await _tick(hass, freezer, 1, settle=False)
    assert len(on) == 3  # three flashes
    assert spoken == []  # speech does not take part in practice mode unless it says so
    assert manager.handlers.last_test is not None and not manager.handlers.testing
    assert not manager.practice.active  # practice mode was only for the test
    assert manager.handlers.problems == {}


async def test_a_handler_that_does_not_start_during_the_test_is_reported(hass, freezer):
    manager = await _house(hass)
    hass.states.async_set("automation.deaf", "on", {"current": 0, "mode": "single", "friendly_name": "Deaf"})
    manager.handlers.known["automation.deaf"] = "Deaf"
    manager.handlers.start_test(quiet=True)
    await _tick(hass, freezer, START_TIMEOUT + 1)
    assert list(manager.handlers.problems) == ["not_started:automation.deaf"]
    assert manager.handlers.last_test["result"] == {"Deaf": "not_started"}
    assert "handler_stalled" in _kinds(manager)


async def test_a_switched_off_automation_is_found_by_the_quiet_check(hass, freezer):
    manager = await _house(hass)
    hass.states.async_set("automation.lights", "off", {"current": 0})
    manager.handlers.known["automation.lights"] = "Lights"
    manager.handlers.check()
    assert list(manager.handlers.problems) == ["disabled:automation.lights"]
    hass.states.async_set("automation.lights", "on", {"current": 0})
    manager.handlers.check()
    assert manager.handlers.problems == {}


async def test_the_daily_check_tests_the_handlers_and_the_weekly_test_is_optional(hass, freezer):
    manager = await _house(hass)
    hass.states.async_set("automation.quiet", "on", {"current": 0, "mode": "single"})
    manager.handlers.known["automation.quiet"] = "Quiet"
    await manager.selftest.async_run_check()
    assert "handler_test" in _kinds(manager)
    assert manager.selftest.status()["handlers_weekly"] is False


async def _failing_service(hass):
    from homeassistant.exceptions import HomeAssistantError as HAError

    async def boom(call):
        raise HAError("boom")

    hass.services.async_register("test", "boom", boom)


async def test_an_automation_that_errors_out_is_stalled_with_the_cause_from_its_trace(hass, freezer):
    manager = await _house(hass)
    await _failing_service(hass)
    await _blueprints(hass, ("run_actions_on_events.yaml", {"partitions": [PANEL], 
        "events": EVENTS, "event_types": ["handler_test"], "in_practice": True, "actions": [{"action": "test.boom"}]}, "own"))
    manager.handlers.start_test(quiet=False)
    await _pump(hass)
    problem = manager.handlers.problems["stalled:automation.handler_own"]
    assert "boom" in problem["detail"]
    assert manager.handlers.last_test["result"] == {"Handler own": "stalled"}


async def test_your_own_actions_stay_out_of_practice_mode_unless_you_say_so(hass, freezer):
    manager = await _house(hass)
    ran = async_mock_service(hass, "test", "ran")
    await _blueprints(hass, ("run_actions_on_events.yaml", {"partitions": [PANEL], 
        "events": EVENTS, "event_types": ["handler_test"], "actions": [{"action": "test.ran"}]}, "own"))
    manager.handlers.start_test(quiet=False)
    await _pump(hass)
    assert ran == [] and manager.handlers.problems == {}  # practice mode: it only reported
    assert manager.handlers.last_test["result"] == {"Handler own": "ok"}


async def test_a_handler_that_waits_for_you_is_never_stalled(hass, freezer):
    manager = await _house(hass)
    hass.states.async_set("input_boolean.ack", "off")
    await _blueprints(hass, ("run_actions_on_events.yaml", {"partitions": [PANEL], 
        "events": EVENTS, "event_types": ["technical_alarm_started"], "in_practice": True,
        "actions": [{"repeat": {"sequence": [{"delay": {"seconds": 30}}],
                                "until": [{"condition": "state", "entity_id": "input_boolean.ack", "state": "on"}]}}]}, "wait"))
    manager.publish("technical_alarm_started", sensor="x")
    await _pump(hass, settle=False)
    assert len(manager.handlers.runs) == 1
    for _ in range(40):  # twenty minutes
        await _tick(hass, freezer, 30, settle=False)
    assert manager.handlers.problems == {} and len(manager.handlers.runs) == 1
    hass.states.async_set("input_boolean.ack", "on")
    await _tick(hass, freezer, 31, settle=False)
    assert manager.handlers.runs == {} and manager.handlers.problems == {}
