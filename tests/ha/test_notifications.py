from __future__ import annotations

import pytest
from homeassistant.config_entries import SOURCE_USER
from homeassistant.data_entry_flow import FlowResultType, InvalidData
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from pytest_homeassistant_custom_component.common import async_mock_service

from .common import EVENTS, PANEL, make_entry, sub
from .test_integration import _call, _setup, _tick


def channel(sid="n1", name="Anna phone", service="mobile_app_anna", categories=("alarm", "arming", "fault"),
            delay=0, priority=False):
    return sub("notification", name, {"service": service, "categories": list(categories),
                                      "delay": delay, "priority": priority}, sid)


async def _house(hass, *channels, **data):
    return await _setup(hass, make_entry(extra_subentries=list(channels), **data))


def _messages(calls):
    return [c.data["message"] for c in calls]


async def test_arming_and_alarm_messages(hass, freezer):
    calls = async_mock_service(hass, "notify", "mobile_app_anna")
    await _house(hass, channel())
    await _call(hass, "alarm_arm_away", code="1234")
    await _tick(hass, freezer, 60)
    hass.states.async_set("binary_sensor.living_pir", "on")
    await hass.async_block_till_done()
    msgs = _messages(calls)
    assert msgs[0] == "Armed (away) by Anna"
    assert msgs[1] == "ALARM: intrusion (Living PIR) No siren is connected."
    assert calls[0].data["title"] == "Vigil Alarm"
    assert "data" not in calls[0].data


async def test_messages_follow_the_language(hass):
    hass.config.language = "nl"
    calls = async_mock_service(hass, "notify", "mobile_app_anna")
    await _house(hass, channel())
    await _call(hass, "alarm_arm_home", code="1234")
    await _call(hass, "alarm_disarm", code="1234")
    assert _messages(calls) == ["Ingeschakeld (home) door Anna", "Uitgeschakeld door Anna"]


async def test_channel_only_gets_its_categories(hass):
    anna = async_mock_service(hass, "notify", "mobile_app_anna")
    bob = async_mock_service(hass, "notify", "mobile_app_bob")
    await _house(hass, channel(categories=("arming",)), channel("n2", "Bob", "mobile_app_bob", categories=("alarm",)))
    await _call(hass, "alarm_arm_home", code="1234")
    hass.states.async_set("binary_sensor.smoke", "on")
    await hass.async_block_till_done()
    assert _messages(anna) == ["Armed (home) by Anna"]
    assert _messages(bob) == ["ALARM: fire (Smoke) No siren is connected."]


async def test_escalation_channel_only_sends_if_the_alarm_is_still_active(hass, freezer):
    first = async_mock_service(hass, "notify", "mobile_app_anna")
    second = async_mock_service(hass, "notify", "mobile_app_bob")
    await _house(hass, channel(categories=("alarm",)),
                 channel("n2", "Escalation", "mobile_app_bob", categories=("alarm",), delay=60))
    hass.states.async_set("binary_sensor.smoke", "on")
    await hass.async_block_till_done()
    assert len(first) == 1 and len(second) == 0
    await _tick(hass, freezer, 59)
    assert len(second) == 0
    await _tick(hass, freezer, 1)
    assert len(second) == 1

    # Second alarm, but disarmed in time: the escalation is cancelled.
    await _call(hass, "alarm_disarm", code="1234")
    hass.states.async_set("binary_sensor.smoke", "off")
    await hass.async_block_till_done()
    hass.states.async_set("binary_sensor.smoke", "on")
    await hass.async_block_till_done()
    assert len(first) == 2
    await _tick(hass, freezer, 30)
    await _call(hass, "alarm_disarm", code="1234")
    await _tick(hass, freezer, 120)
    assert len(second) == 1


async def test_the_delay_only_applies_to_alarm_messages(hass, freezer):
    calls = async_mock_service(hass, "notify", "mobile_app_anna")
    await _house(hass, channel(categories=("alarm", "arming"), delay=60))
    await _call(hass, "alarm_arm_home", code="1234")
    assert _messages(calls) == ["Armed (home) by Anna"]  # not delayed


async def test_alarm_ending_by_itself_cancels_the_escalation(hass, freezer):
    calls = async_mock_service(hass, "notify", "mobile_app_bob")
    await _house(hass, channel("n2", "Escalation", "mobile_app_bob", categories=("alarm",), delay=60),
                 trigger_time=30)
    hass.states.async_set("binary_sensor.smoke", "on")
    await hass.async_block_till_done()
    await _tick(hass, freezer, 30)  # the alarm duration is over
    assert hass.states.get(PANEL).state == "disarmed"
    await _tick(hass, freezer, 60)
    assert len(calls) == 0


async def test_priority_data_only_on_alarm_messages(hass):
    calls = async_mock_service(hass, "notify", "mobile_app_anna")
    await _house(hass, channel(priority=True))
    await _call(hass, "alarm_arm_home", code="1234")
    hass.states.async_set("binary_sensor.smoke", "on")
    await hass.async_block_till_done()
    assert "data" not in calls[0].data
    assert calls[1].data["data"]["push"]["interruption-level"] == "critical"
    assert calls[1].data["data"]["priority"] == "high"


async def test_a_failing_notify_service_is_reported_and_does_not_break_the_alarm(hass):
    async def broken(call):
        raise HomeAssistantError("phone offline")

    hass.services.async_register("notify", "mobile_app_anna", broken)
    await _house(hass, channel())
    hass.states.async_set("binary_sensor.smoke", "on")
    await hass.async_block_till_done()
    assert hass.states.get(PANEL).state == "triggered"
    attrs = hass.states.get(EVENTS).attributes
    assert attrs["event_type"] == "notification_failed" and attrs["channel"] == "Anna phone"
    assert "phone offline" in attrs["error"]


async def test_test_service(hass):
    anna = async_mock_service(hass, "notify", "mobile_app_anna")
    bob = async_mock_service(hass, "notify", "mobile_app_bob")
    await _house(hass, channel(), channel("n2", "Bob", "mobile_app_bob"))
    await hass.services.async_call("vigil", "test_notification", {}, blocking=True)
    assert _messages(anna) == ["Test notification from Vigil Alarm"] == _messages(bob)
    await hass.services.async_call("vigil", "test_notification", {"channel": "Bob"}, blocking=True)
    assert len(anna) == 1 and len(bob) == 2


async def test_test_service_without_channels_says_so(hass):
    await _house(hass)
    with pytest.raises(ServiceValidationError, match="No notification channel"):
        await hass.services.async_call("vigil", "test_notification", {}, blocking=True)


async def test_the_alarm_works_without_any_channel(hass):
    await _house(hass)
    hass.states.async_set("binary_sensor.smoke", "on")
    await hass.async_block_till_done()
    assert hass.states.get(PANEL).state == "triggered"


async def test_escalation_continues_after_a_restart_during_the_alarm(hass, freezer):
    immediate = async_mock_service(hass, "notify", "mobile_app_anna")
    escalation = async_mock_service(hass, "notify", "mobile_app_bob")
    entry = await _house(hass, channel(categories=("alarm",)),
                         channel("n2", "Escalation", "mobile_app_bob", categories=("alarm",), delay=60))
    hass.states.async_set("binary_sensor.smoke", "on")
    await hass.async_block_till_done()
    assert len(immediate) == 1
    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    assert len(immediate) == 1  # not repeated
    await _tick(hass, freezer, 60)
    assert len(escalation) == 1 and "ALARM: fire" in escalation[0].data["message"]
