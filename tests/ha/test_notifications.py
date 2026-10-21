from __future__ import annotations

import pytest
from homeassistant.config_entries import SOURCE_USER
from homeassistant.data_entry_flow import FlowResultType, InvalidData
from homeassistant.exceptions import HomeAssistantError
from custom_components.vigil_alarm.errors import VigilError as ServiceValidationError
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
    await hass.services.async_call("vigil_alarm", "test_notification", {}, blocking=True)
    assert _messages(anna) == ["Test notification from Vigil Alarm"] == _messages(bob)
    await hass.services.async_call("vigil_alarm", "test_notification", {"channel": "Bob"}, blocking=True)
    assert len(anna) == 1 and len(bob) == 2


async def test_test_service_without_channels_says_so(hass):
    await _house(hass)
    with pytest.raises(ServiceValidationError, match="No notification channel"):
        await hass.services.async_call("vigil_alarm", "test_notification", {}, blocking=True)


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


async def test_a_lockout_is_reported_on_the_fault_channels(hass):
    from .test_control_points import _vigil

    calls = async_mock_service(hass, "notify", "mobile_app_anna")
    await _house(hass, channel(categories=("fault",)))
    for _ in range(5):
        with pytest.raises(ServiceValidationError):
            await _vigil(hass, "disarm", code="0000", source="panel garage")
    assert _messages(calls) == ["Too many wrong codes at panel garage: locked for 5 minutes"]


async def test_notify_groups_are_not_offered_but_an_older_channel_with_one_keeps_working(hass):
    """0.6.10: notify entities (groups made as a helper) are not offered any more, because they cannot send an alarm
    with a high priority; a channel saved with one in 0.5.5 to 0.6.9 still sends, with a title and a message."""
    from custom_components.vigil_alarm.editing import notify_services

    calls = async_mock_service(hass, "notify", "send_message")
    hass.states.async_set("notify.family", "unknown")
    await _house(hass, channel(sid="grp", name="Family", service="notify.family", priority=True))
    assert "notify.family" not in notify_services(hass)
    await _call(hass, "alarm_arm_home", code="1234")
    assert [c.data["message"] for c in calls] == ["Armed (home) by Anna"]
    assert calls[0].data["entity_id"] == "notify.family" and calls[0].data["title"] == "Vigil Alarm"
    assert "data" not in calls[0].data  # no app specific data for an entity


async def test_a_channel_can_have_several_services_and_one_that_fails_does_not_stop_the_others(hass):
    """0.6.10: several people get the same message from one channel; a failing service is reported and the rest go on."""
    anna = async_mock_service(hass, "notify", "mobile_app_anna")
    bob = async_mock_service(hass, "notify", "mobile_app_bob")
    broken = async_mock_service(hass, "notify", "mobile_app_broken", raise_exception=RuntimeError("offline"))
    item = sub("notification", "Family", {"services": ["mobile_app_broken", "mobile_app_anna", "mobile_app_bob"],
                                          "categories": ["alarm", "arming"], "delay": 0, "priority": True}, "fam")
    await _house(hass, item)
    await _call(hass, "alarm_arm_home", code="1234")
    await hass.async_block_till_done()
    assert [c.data["message"] for c in anna] == ["Armed (home) by Anna"] == [c.data["message"] for c in bob]
    assert len(broken) == 1
    attrs = hass.states.get(EVENTS).attributes
    assert attrs["event_type"] == "notification_failed" and attrs["channel"] == "Family" and attrs["service"] == "mobile_app_broken"


async def test_a_channel_is_saved_with_a_list_of_services(hass):
    """The form gives `services` (or an older `service`); the channel keeps a list, every service must exist."""
    import pytest

    from custom_components.vigil_alarm.editing import EditError, async_prepare
    from custom_components.vigil_alarm.items import channel_services

    async_mock_service(hass, "notify", "mobile_app_anna")
    async_mock_service(hass, "notify", "mobile_app_bob")
    entry = await _house(hass)
    raw = {"name": "Family", "categories": ["alarm"], "delay": 0}
    _name, data = await async_prepare(hass, entry, "notification", None, {**raw, "services": ["mobile_app_anna", "mobile_app_bob", "mobile_app_anna"]})
    assert data["services"] == ["mobile_app_anna", "mobile_app_bob"] and "service" not in data
    _name, data = await async_prepare(hass, entry, "notification", None, {**raw, "service": "mobile_app_anna"})  # an older form
    assert data["services"] == ["mobile_app_anna"]
    for bad in ({"services": []}, {"services": ["mobile_app_anna", "notify.family"]}, {"services": ["nope"]}, {}):
        with pytest.raises(EditError) as err:
            await async_prepare(hass, entry, "notification", None, {**raw, **bad})
        assert err.value.errors == {"services": "service_not_found"}
    assert channel_services({"service": "mobile_app_anna"}) == ["mobile_app_anna"]
    assert channel_services({"services": ["a", "b"], "service": "old"}) == ["a", "b"]
