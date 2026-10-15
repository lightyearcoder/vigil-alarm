"""The blueprints, run for real against the integration: every file loads and does what it says."""

from __future__ import annotations

import asyncio
import pathlib
import shutil
from datetime import timedelta

import pytest
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import async_fire_time_changed, async_mock_service

from .common import EVENTS, PANEL, make_entry
from .test_integration import _call, _setup, _tick

BLUEPRINTS = pathlib.Path(__file__).parents[2] / "blueprints" / "automation" / "vigil_alarm"


async def _settle(hass):
    # Events travel through call_soon callbacks, which block_till_done does not see: give them turns.
    for _ in range(4):
        await asyncio.sleep(0)
        await hass.async_block_till_done()


async def _pump(hass, turns=30):
    """Let queued callbacks and tasks run without waiting for the flashing loop, which never ends by itself."""
    for _ in range(turns):
        await asyncio.sleep(0)


async def _flash_tick(hass, freezer, seconds):
    freezer.tick(timedelta(seconds=seconds))
    async_fire_time_changed(hass, dt_util.utcnow())
    await _pump(hass)


async def _automation(hass, name, inputs):
    target = pathlib.Path(hass.config.path("blueprints/automation/vigil_alarm"))
    target.mkdir(parents=True, exist_ok=True)
    shutil.copy(BLUEPRINTS / name, target / name)
    assert await async_setup_component(
        hass, "automation", {"automation": [{"use_blueprint": {"path": f"vigil_alarm/{name}", "input": inputs}}]}
    )
    await _settle(hass)


def test_every_blueprint_is_valid_and_documented():
    import yaml

    class Loader(yaml.SafeLoader):
        pass

    Loader.add_constructor("!input", lambda loader, node: f"<{node.value}>")
    files = sorted(BLUEPRINTS.glob("*.yaml"))
    assert len(files) >= 6
    for path in files:
        data = yaml.load(path.read_text(), Loader)  # noqa: S506 (our own files)
        bp = data["blueprint"]
        assert bp["domain"] == "automation" and bp["name"].startswith("Vigil - ") and bp["description"], path
        assert bp["source_url"].endswith(f"blueprints/automation/vigil_alarm/{path.name}"), path
        used = set()
        text = path.read_text()
        for name in bp["input"]:
            used.add(name)
            assert f"!input {name}" in text, f"{path.name}: input {name} is never used"
        for line in text.splitlines():
            if "!input " in line:
                assert line.split("!input ")[1].strip() in used, (path.name, line)


async def test_lights_flash_during_an_alarm_and_come_back(hass, freezer):
    await _setup(hass)
    await _automation(hass, "flash_lights_on_alarm.yaml", {
        "events": EVENTS, "alarm": PANEL, "lights": ["light.hall"], "causes": ["fire"], "interval": 2})
    on = async_mock_service(hass, "light", "turn_on")
    off = async_mock_service(hass, "light", "turn_off")
    create = async_mock_service(hass, "scene", "create")
    restore = async_mock_service(hass, "scene", "turn_on")
    delete = async_mock_service(hass, "scene", "delete")

    hass.states.async_set("binary_sensor.smoke", "on")
    await _pump(hass)
    assert hass.states.get(PANEL).state == "triggered"
    assert create[0].data["snapshot_entities"] == ["light.hall"] and create[0].data["scene_id"] == "vigil_lights_before"
    assert len(on) == 1 and on[0].data["rgb_color"] == [255, 0, 0] and on[0].data["brightness_pct"] == 100
    await _flash_tick(hass, freezer, 2)
    assert len(off) == 1
    await _flash_tick(hass, freezer, 2)
    assert len(on) == 2  # keeps flashing

    # the scene exists now (the mocked service does not create it)
    hass.states.async_set("scene.vigil_lights_before", "unknown")
    await _call(hass, "alarm_disarm", code="1234")
    await _pump(hass)
    assert restore[-1].data["entity_id"] == ["scene.vigil_lights_before"]
    assert delete[-1].data["entity_id"] == ["scene.vigil_lights_before"]
    flashes = len(on)
    await _flash_tick(hass, freezer, 10)
    assert len(on) == flashes  # stopped


async def test_lights_ignore_causes_that_were_not_chosen_and_stop_at_the_limit(hass, freezer):
    await _setup(hass)
    await _automation(hass, "flash_lights_on_alarm.yaml", {
        "events": EVENTS, "alarm": PANEL, "lights": ["light.hall"], "causes": ["intrusion"],
        "interval": 1, "max_duration": 10})
    on = async_mock_service(hass, "light", "turn_on")
    async_mock_service(hass, "light", "turn_off")
    create = async_mock_service(hass, "scene", "create")
    restore = async_mock_service(hass, "scene", "turn_on")
    async_mock_service(hass, "scene", "delete")
    hass.states.async_set("binary_sensor.smoke", "on")
    await _pump(hass)
    assert hass.states.get(PANEL).state == "triggered" and create == [] and on == []

    # intrusion is chosen: flashing stops by itself after max_duration even if the alarm goes on
    await _call(hass, "alarm_disarm", code="1234")
    hass.states.async_set("binary_sensor.smoke", "off")
    await _pump(hass)
    await _call(hass, "alarm_arm_home", code="1234")
    await _pump(hass)
    assert hass.states.get(PANEL).state == "armed_home"
    hass.states.async_set("binary_sensor.front_door", "on")
    await _pump(hass)
    await _flash_tick(hass, freezer, 30)  # entry delay passes
    assert hass.states.get(PANEL).state == "triggered"
    for _ in range(14):
        await _flash_tick(hass, freezer, 1)
    assert len(create) == 1
    flashes = len(on)
    assert 4 <= flashes <= 6  # 10 seconds at 1s on + 1s off
    assert restore  # put back at the limit
    await _flash_tick(hass, freezer, 20)
    assert len(on) == flashes


async def test_speech_messages(hass, freezer):
    speak = async_mock_service(hass, "tts", "speak")
    await _setup(hass)
    await _automation(hass, "announce_with_speech.yaml", {
        "events": EVENTS, "tts": "tts.home", "speakers": ["media_player.kitchen"],
        "msg_arming_started": "", "msg_armed": "Armed in {{ trigger.to_state.attributes.mode }} by {{ trigger.to_state.attributes.user }}",
        "msg_disarmed": "Disarmed", "msg_pending_started": "", "msg_triggered": "Alarm {{ trigger.to_state.attributes.cause }}"})
    await _call(hass, "alarm_arm_away", code="1234")
    await _settle(hass)
    assert speak == []  # empty message = silent
    await _tick(hass, freezer, 60)
    assert [c.data["message"] for c in speak] == ["Armed in away by Anna"]
    assert speak[0].data["media_player_entity_id"] == ["media_player.kitchen"]
    hass.states.async_set("binary_sensor.smoke", "on")
    await _settle(hass)
    assert speak[-1].data["message"] == "Alarm fire"
    await _call(hass, "alarm_disarm", code="1234")
    await _settle(hass)
    assert speak[-1].data["message"] == "Disarmed"


async def test_arm_when_everyone_has_left(hass, freezer):
    notify = async_mock_service(hass, "notify", "send_message")
    await _setup(hass)
    hass.states.async_set("person.anna", "home")
    hass.states.async_set("person.bob", "home")
    await _automation(hass, "arm_when_everyone_leaves.yaml", {
        "alarm": PANEL, "persons": ["person.anna", "person.bob"], "wait": 3, "mode": "away", "code": "1234",
        "notify": ["notify.phone"]})
    hass.states.async_set("person.anna", "not_home")
    await _settle(hass)
    await _tick(hass, freezer, 240)
    assert hass.states.get(PANEL).state == "disarmed"  # Bob is still home
    hass.states.async_set("person.bob", "not_home")
    await _settle(hass)
    await _tick(hass, freezer, 120)
    assert hass.states.get(PANEL).state == "disarmed"  # not away long enough yet
    await _tick(hass, freezer, 70)
    assert hass.states.get(PANEL).state == "arming" and notify == []
    await _tick(hass, freezer, 60)
    assert hass.states.get(PANEL).state == "armed_away"
    assert hass.states.get(PANEL).attributes["changed_by"] == "Anna"


async def test_arming_that_is_refused_sends_a_message(hass, freezer):
    notify = async_mock_service(hass, "notify", "send_message")
    await _setup(hass)
    hass.states.async_set("person.anna", "home")
    await _automation(hass, "arm_when_everyone_leaves.yaml", {
        "alarm": PANEL, "persons": ["person.anna"], "wait": 1, "mode": "away", "code": "1234",
        "notify": ["notify.phone"]})
    hass.states.async_set("binary_sensor.living_pir", "unavailable")  # blocks arming away
    await _settle(hass)
    hass.states.async_set("person.anna", "not_home")
    await _settle(hass)
    await _tick(hass, freezer, 61)
    assert hass.states.get(PANEL).state == "disarmed"
    assert len(notify) == 1 and "could not be armed" in notify[0].data["message"]
    assert notify[0].data["entity_id"] == ["notify.phone"]


async def test_arming_that_is_refused_without_a_message_target_stays_quiet(hass, freezer):
    notify = async_mock_service(hass, "notify", "send_message")
    await _setup(hass)
    hass.states.async_set("person.anna", "home")
    await _automation(hass, "arm_when_everyone_leaves.yaml", {
        "alarm": PANEL, "persons": ["person.anna"], "wait": 1, "mode": "away", "code": "1234"})
    hass.states.async_set("binary_sensor.living_pir", "unavailable")
    await _settle(hass)
    hass.states.async_set("person.anna", "not_home")
    await _settle(hass)
    await _tick(hass, freezer, 61)
    assert hass.states.get(PANEL).state == "disarmed" and notify == []


async def test_arm_on_schedule(hass, freezer):
    await hass.config.async_set_time_zone("UTC")
    freezer.move_to("2026-10-13 22:59:30+00:00")  # a Tuesday
    await _setup(hass)
    await _automation(hass, "arm_on_schedule.yaml", {
        "alarm": PANEL, "time": "23:00:00", "days": ["tue"], "mode": "night", "code": "1234"})
    await _tick(hass, freezer, 40)
    assert hass.states.get(PANEL).state == "arming"  # night has a 10 second exit delay
    await _tick(hass, freezer, 15)
    assert hass.states.get(PANEL).state == "armed_night"


async def test_schedule_skips_days_that_were_not_chosen(hass, freezer):
    await hass.config.async_set_time_zone("UTC")
    freezer.move_to("2026-10-13 22:59:30+00:00")  # a Tuesday
    await _setup(hass)
    await _automation(hass, "arm_on_schedule.yaml", {
        "alarm": PANEL, "time": "23:00:00", "days": ["mon", "wed"], "mode": "night", "code": "1234"})
    await _tick(hass, freezer, 40)
    assert hass.states.get(PANEL).state == "disarmed"


async def test_arrival_reminder_only_while_armed(hass, freezer):
    notify = async_mock_service(hass, "notify", "send_message")
    await _setup(hass)
    hass.states.async_set("person.anna", "not_home")
    await _automation(hass, "arrival_reminder.yaml", {
        "alarm": PANEL, "persons": ["person.anna"], "notify": ["notify.phone"]})
    hass.states.async_set("person.anna", "home")
    await _settle(hass)
    assert notify == []  # disarmed: nothing to remind
    hass.states.async_set("person.anna", "not_home")
    await _call(hass, "alarm_arm_home", code="1234")
    await _settle(hass)
    assert hass.states.get(PANEL).state == "armed_home"
    hass.states.async_set("person.anna", "home")
    await _settle(hass)
    assert len(notify) == 1 and "still armed" in notify[0].data["message"]


async def test_run_your_own_actions_on_chosen_events(hass, freezer):
    calls = async_mock_service(hass, "test", "seen")
    await _setup(hass)
    await _automation(hass, "run_actions_on_events.yaml", {
        "events": EVENTS, "event_types": ["triggered", "disarmed"],
        "actions": [{"action": "test.seen", "data": {"what": "{{ event_type }}", "cause": "{{ data.cause | default('') }}"}}]})
    await _call(hass, "alarm_arm_home", code="1234")
    await _settle(hass)
    assert calls == []  # armed is not in the list
    hass.states.async_set("binary_sensor.smoke", "on")
    await _settle(hass)
    assert [(c.data["what"], c.data["cause"]) for c in calls] == [("triggered", "fire")]
    await _call(hass, "alarm_disarm", code="1234")
    await _settle(hass)
    assert [c.data["what"] for c in calls] == ["triggered", "disarmed"]
