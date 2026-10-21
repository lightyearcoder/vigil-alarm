from __future__ import annotations

import pytest
from homeassistant.config_entries import SOURCE_USER
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.exceptions import HomeAssistantError
from custom_components.vigil_alarm.errors import VigilError as ServiceValidationError
from pytest_homeassistant_custom_component.common import async_mock_service

from .common import EVENTS, PANEL, make_entry, sub
from .test_integration import _call, _setup, _tick


def siren(sid="s1", name="Hall siren", **over):
    data = {"control": "switch.siren", "causes": ["intrusion", "fire", "gas", "tamper", "fault"],
            "max_duration": 180, "repeat_every": 0}
    data.update(over)
    return sub("siren", name, data, sid)


GAS = sub("zone", "Kitchen gas", {"entity_id": "binary_sensor.gas", "cls": "gas", "gas_type": "natural_gas"}, "gas")
CO = sub("zone", "Living CO", {"entity_id": "binary_sensor.co", "cls": "gas", "gas_type": "co"}, "co")


_PENDING: dict = {}


class Mocks:
    """Fake services. They are installed after the integration is set up, because
    setting up the switch/select/number platforms registers the real services."""

    def __init__(self, hass):
        self.hass = hass
        self.on = self.off = self.select = self.number = self.notify = []
        _PENDING[hass] = self

    def install(self):
        hass = self.hass
        self.on = async_mock_service(hass, "switch", "turn_on")
        self.off = async_mock_service(hass, "switch", "turn_off")
        self.select = async_mock_service(hass, "select", "select_option")
        self.number = async_mock_service(hass, "number", "set_value")
        self.notify = async_mock_service(hass, "notify", "mobile_app_anna")

    def targets(self, calls):
        return [c.data["entity_id"] for c in calls]


async def _house(hass, *extra, **data):
    for name in ("gas", "co"):
        hass.states.async_set(f"binary_sensor.{name}", "off")
    entry = await _setup(hass, make_entry(extra_subentries=list(extra), **data))
    if hass in _PENDING:
        _PENDING.pop(hass).install()
    return entry


def _record(hass, entry):
    from homeassistant.core import callback
    from custom_components.vigil_alarm.manager import SIGNAL_EVENT
    from homeassistant.helpers.dispatcher import async_dispatcher_connect

    seen: list[str] = []
    async_dispatcher_connect(hass, SIGNAL_EVENT.format(entry.entry_id), callback(lambda e: seen.append(e["type"])))
    return seen


async def test_siren_sounds_on_alarm_and_stops_at_disarm(hass):
    m = Mocks(hass)
    hass.states.async_set("switch.siren", "on")
    entry = await _house(hass, siren())
    seen = _record(hass, entry)
    hass.states.async_set("binary_sensor.smoke", "on")
    await hass.async_block_till_done()
    assert m.targets(m.on) == ["switch.siren"]
    events = hass.states.get(EVENTS).attributes
    assert events["event_type"] == "siren_started" and events["verified"] is True
    await _call(hass, "alarm_disarm", code="1234")
    await hass.async_block_till_done()
    assert m.targets(m.off) == ["switch.siren"]
    assert "siren_stopped" in seen


async def test_unverifiable_siren_is_reported_as_such(hass):
    Mocks(hass)
    hass.states.async_set("switch.siren", "off")  # e.g. a siren that cannot report its state
    await _house(hass, siren())
    hass.states.async_set("binary_sensor.smoke", "on")
    await hass.async_block_till_done()
    assert hass.states.get(EVENTS).attributes["verified"] is False


async def test_siren_only_sounds_for_its_causes(hass):
    m = Mocks(hass)
    await _house(hass, siren(causes=["fire"]))
    await _call(hass, "alarm_arm_home", code="1234")
    hass.states.async_set("binary_sensor.front_door", "on")
    hass.states.async_set("binary_sensor.tamper", "on")
    await hass.async_block_till_done()
    assert hass.states.get(PANEL).state == "triggered"
    assert m.on == []  # tamper alarm, but this siren is fire only


async def test_tone_and_volume_are_set_for_the_cause_and_restored(hass, freezer):
    m = Mocks(hass)
    hass.states.async_set("select.siren_tone", "calm")
    hass.states.async_set("number.siren_volume", "1")
    await _house(hass, siren(tone_entity="select.siren_tone", volume_entity="number.siren_volume",
                             fire={"tone": "loud_fire", "volume": "3"}))
    hass.states.async_set("binary_sensor.smoke", "on")
    await hass.async_block_till_done()
    assert m.select[-1].data == {"entity_id": "select.siren_tone", "option": "loud_fire"}
    assert m.number[-1].data == {"entity_id": "number.siren_volume", "value": 3.0}
    # settings first, then the siren itself
    await _call(hass, "alarm_disarm", code="1234")
    await hass.async_block_till_done()
    assert m.select[-1].data["option"] == "calm" and m.number[-1].data["value"] == 1.0


async def test_cause_change_updates_the_profile_but_restores_the_original(hass, freezer):
    m = Mocks(hass)
    hass.states.async_set("select.siren_tone", "calm")
    await _house(hass, siren(tone_entity="select.siren_tone",
                             intrusion={"tone": "burglar"}, fire={"tone": "fire"}))

    async def select_option(call):  # a select that really changes, like the device would
        m.select.append(call)
        hass.states.async_set(call.data["entity_id"], call.data["option"])

    hass.services.async_register("select", "select_option", select_option)
    await _call(hass, "alarm_arm_home", code="1234")
    hass.states.async_set("binary_sensor.front_door", "on")
    await hass.async_block_till_done()
    await _tick(hass, freezer, 30)
    assert m.select[-1].data["option"] == "burglar"
    hass.states.async_set("binary_sensor.smoke", "on")
    await hass.async_block_till_done()
    assert m.select[-1].data["option"] == "fire"
    await _call(hass, "alarm_disarm", code="1234")
    await hass.async_block_till_done()
    assert m.select[-1].data["option"] == "calm"  # the original, not the burglar tone


async def test_flash_light_but_not_near_flammable_gas(hass):
    m = Mocks(hass)
    await _house(hass, siren(light="switch.flash"), GAS, CO)
    hass.states.async_set("binary_sensor.gas", "on")
    await hass.async_block_till_done()
    assert m.targets(m.on) == ["switch.siren"]  # natural gas: siren only
    await _call(hass, "alarm_disarm", code="1234")
    hass.states.async_set("binary_sensor.gas", "off")
    await hass.async_block_till_done()
    m.on.clear()
    hass.states.async_set("binary_sensor.co", "on")
    await hass.async_block_till_done()
    assert sorted(m.targets(m.on)) == ["switch.flash", "switch.siren"]  # CO: flashing is fine
    await _call(hass, "alarm_disarm", code="1234")
    await hass.async_block_till_done()
    assert "switch.flash" in m.targets(m.off)


async def test_siren_stops_after_the_maximum_time_while_the_alarm_continues(hass, freezer):
    m = Mocks(hass)
    hass.states.async_set("select.siren_tone", "calm")
    await _house(hass, siren(max_duration=30, tone_entity="select.siren_tone", fire={"tone": "fire"}))
    hass.states.async_set("binary_sensor.smoke", "on")
    await hass.async_block_till_done()
    await _tick(hass, freezer, 30)
    assert m.targets(m.off) == ["switch.siren"]
    assert hass.states.get(PANEL).state == "triggered"
    assert m.select[-1].data["option"] == "calm"
    assert hass.states.get(EVENTS).attributes["reason"] == "max_duration"


async def test_siren_that_stops_by_itself_is_switched_on_again(hass, freezer):
    m = Mocks(hass)
    await _house(hass, siren(repeat_every=10))
    hass.states.async_set("binary_sensor.smoke", "on")
    await hass.async_block_till_done()
    assert len(m.on) == 1
    await _tick(hass, freezer, 10)
    await _tick(hass, freezer, 10)
    assert len(m.on) == 3
    await _call(hass, "alarm_disarm", code="1234")
    await hass.async_block_till_done()
    await _tick(hass, freezer, 30)
    assert len(m.on) == 3  # no more repeats after the alarm


async def test_failing_siren_is_reported_and_a_failing_tone_does_not_keep_it_quiet(hass):
    m = Mocks(hass)

    async def broken(call):
        raise HomeAssistantError("zigbee timeout")

    hass.states.async_set("select.siren_tone", "calm")
    await _house(hass, siren(tone_entity="select.siren_tone", fire={"tone": "fire"}),
                 sub("notification", "Anna", {"service": "mobile_app_anna", "categories": ["fault"], "delay": 0, "priority": False}, "n1"))
    hass.services.async_register("select", "select_option", broken)
    hass.states.async_set("binary_sensor.smoke", "on")
    await hass.async_block_till_done()
    assert m.targets(m.on) == ["switch.siren"]  # still sounded
    assert any("Hall siren failed (zigbee timeout)" in c.data["message"] for c in m.notify)


async def test_siren_that_cannot_be_switched_on_says_so(hass):
    m = Mocks(hass)

    async def broken(call):
        raise HomeAssistantError("offline")

    await _house(hass, siren(),
                 sub("notification", "Anna", {"service": "mobile_app_anna", "categories": ["fault"], "delay": 0, "priority": False}, "n1"))
    hass.services.async_register("switch", "turn_on", broken)
    hass.states.async_set("binary_sensor.smoke", "on")
    await hass.async_block_till_done()
    assert hass.states.get(PANEL).state == "triggered"
    assert [c.data["message"] for c in m.notify] == ["Siren Hall siren failed (offline)"]
    assert not any(e for e in [hass.states.get(EVENTS).attributes] if e["event_type"] == "siren_started")


async def test_alarm_ended_right_after_it_started_leaves_the_siren_off(hass):
    m = Mocks(hass)
    await _house(hass, siren())
    hass.states.async_set("binary_sensor.smoke", "on")
    await _call(hass, "alarm_disarm", code="1234")  # no waiting in between
    await hass.async_block_till_done()
    assert m.targets(m.on) == ["switch.siren"] and m.targets(m.off) == ["switch.siren"]


async def test_siren_sounds_again_after_a_restart_during_the_alarm(hass):
    m = Mocks(hass)
    entry = await _house(hass, siren())
    hass.states.async_set("binary_sensor.smoke", "on")
    await hass.async_block_till_done()
    assert len(m.on) == 1
    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    assert len(m.on) == 2


async def test_alarm_message_mentions_a_missing_siren_only_when_there_is_none(hass):
    m = Mocks(hass)
    notif = sub("notification", "Anna", {"service": "mobile_app_anna", "categories": ["alarm"], "delay": 0, "priority": False}, "n1")
    await _house(hass, notif, siren())
    hass.states.async_set("binary_sensor.smoke", "on")
    await hass.async_block_till_done()
    assert m.notify[0].data["message"] == "ALARM: fire (Smoke)"


async def test_test_siren_service(hass, freezer):
    m = Mocks(hass)
    await _house(hass, siren())
    await hass.services.async_call("vigil_alarm", "test_siren", {"duration": 5}, blocking=True)
    assert m.targets(m.on) == ["switch.siren"] and m.off == []
    await _tick(hass, freezer, 5)
    assert m.targets(m.off) == ["switch.siren"]
    hass.states.async_set("binary_sensor.smoke", "on")
    await hass.async_block_till_done()
    with pytest.raises(ServiceValidationError, match="alarm is active"):
        await hass.services.async_call("vigil_alarm", "test_siren", {}, blocking=True)


async def test_test_siren_without_sirens(hass):
    Mocks(hass)
    await _house(hass)
    with pytest.raises(ServiceValidationError, match="No siren"):
        await hass.services.async_call("vigil_alarm", "test_siren", {}, blocking=True)


async def test_test_siren_does_not_silence_a_real_alarm(hass, freezer):
    m = Mocks(hass)
    await _house(hass, siren())
    await hass.services.async_call("vigil_alarm", "test_siren", {"duration": 5}, blocking=True)
    hass.states.async_set("binary_sensor.smoke", "on")
    await hass.async_block_till_done()
    await _tick(hass, freezer, 5)
    assert m.off == []


async def test_sensor_fault_alarm_uses_the_intrusion_sound(hass, freezer):
    m = Mocks(hass)
    window = sub("zone", "Window", {"entity_id": "binary_sensor.window", "cls": "intrusion", "type": "instant",
                                    "sensor_groups": ["g_home"], "on_unavailable": "trigger"}, "window")
    hass.states.async_set("binary_sensor.window", "off")
    hass.states.async_set("select.siren_tone", "calm")
    await _house(hass, window, siren(tone_entity="select.siren_tone", intrusion={"tone": "burglar"}))
    await _call(hass, "alarm_arm_home", code="1234")
    hass.states.async_set("binary_sensor.window", "unavailable")
    await hass.async_block_till_done()
    assert hass.states.get(PANEL).attributes["cause"] == "fault"
    assert m.select[-1].data["option"] == "burglar"


async def test_the_last_start_of_a_siren_says_confirmed_sent_or_failed(hass, freezer):
    """The self-test card shows what the last start came to, so a siren that cannot confirm is not mistaken for
    one that does."""
    from homeassistant.exceptions import HomeAssistantError
    from .common import PANEL  # noqa: F401

    entry = await _setup(hass, make_entry(extra_subentries=[siren()]))
    manager = entry.runtime_data
    assert manager.selftest.status()["siren_starts"] == []
    hass.states.async_set("switch.siren", "off")
    calls = async_mock_service(hass, "switch", "turn_on")
    await manager.sirens._async_start(manager.sirens.sirens[0], "intrusion", None)
    assert [s["result"] for s in manager.selftest.status()["siren_starts"]] == ["sent"]  # it did not turn on by itself
    hass.states.async_set("switch.siren", "on")
    await manager.sirens._async_start(manager.sirens.sirens[0], "intrusion", None)
    assert manager.selftest.status()["siren_starts"][0]["result"] == "confirmed"

    def broken(call):
        raise HomeAssistantError("offline")

    hass.services.async_register("switch", "turn_on", broken)
    await manager.sirens._async_start(manager.sirens.sirens[0], "intrusion", None)
    only = manager.selftest.status()["siren_starts"]
    assert len(only) == 1 and only[0]["result"] == "failed" and only[0]["name"] == "Hall siren" and only[0]["at"]
    assert calls
