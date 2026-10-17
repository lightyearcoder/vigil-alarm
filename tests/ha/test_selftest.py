from __future__ import annotations

from datetime import timedelta

from homeassistant.helpers import issue_registry as ir

from custom_components.vigil_alarm.const import DOMAIN

from .common import sub
from .test_panel import _ws
from .test_sirens import Mocks, _house, siren
from .test_supervision import NOTIFY

NOON_PACIFIC = "2026-10-15 19:00:00+00:00"  # 12:00 in the test time zone
NIGHT_PACIFIC = "2026-10-15 10:00:00+00:00"  # 03:00


def issues(hass):
    return {i.translation_key for i in ir.async_get(hass).issues.values() if i.domain == DOMAIN}


def sent(m):
    return [c.data["message"] for c in m.notify]


async def _ready(hass, freezer, when=NOON_PACIFIC, **data):
    freezer.move_to(when)
    m = Mocks(hass)
    entry = await _house(hass, siren(), NOTIFY, **data)
    return m, entry, entry.runtime_data.selftest


async def test_the_quiet_check_says_nothing_when_all_is_well(hass, freezer):
    hass.states.async_set("switch.siren", "off")
    m, entry, st = await _ready(hass, freezer)
    await st._tick()
    status = st.status()
    assert status["last_check"] and status["problems"] == []
    assert sent(m) == [] and issues(hass) == set()


async def test_a_channel_that_no_longer_exists_is_found_and_reported(hass, freezer):
    hass.states.async_set("switch.siren", "off")
    m, entry, st = await _ready(hass, freezer)
    other = sub("notification", "Old phone", {"service": "mobile_app_gone", "categories": ["fault"], "delay": 0, "priority": False}, "n9")
    st.entry.options["items"]["n9"] = {"type": "notification", "title": other["title"], "data": other["data"]}
    await st._tick()
    assert {"code": "channel_missing", "name": "Old phone"} in st.status()["problems"]
    assert "Self-check found a problem: Old phone" in "".join(sent(m))
    assert issues(hass) == {"selftest_channel_missing"}


async def test_a_siren_that_cannot_be_reached_shows_in_the_check(hass, freezer):
    m, entry, st = await _ready(hass, freezer)  # switch.siren has no state
    await st._tick()
    assert {"code": "siren_unavailable", "name": "Hall siren"} in st.status()["problems"]


async def test_reminder_then_second_reminder_then_a_repair_and_a_test_clears_it(hass, freezer):
    hass.states.async_set("switch.siren", "off")
    m, entry, st = await _ready(hass, freezer)
    await st._tick()
    assert sent(m) == [] and st.status()["due"]
    freezer.tick(timedelta(days=31))
    await st._tick()
    assert sent(m)[-1].startswith("Monthly test of the alarm")
    assert m.notify[-1].data["data"]["actions"][0]["action"] == "VIGIL_TEST_SIREN"  # a mobile_app channel
    count = len(m.notify)
    await st._tick()
    assert len(m.notify) == count  # not again the same day
    freezer.tick(timedelta(days=3))
    await st._tick()
    assert sent(m)[-1].startswith("Reminder:")
    freezer.tick(timedelta(days=6))
    await st._tick()
    await hass.async_block_till_done()
    assert st.status()["overdue_days"] >= 37 and "selftest_overdue" in issues(hass)
    await hass.services.async_call("vigil_alarm", "test_siren", {"duration": 2}, blocking=True)
    assert st.status()["reminders"] == 0 and st.status()["overdue_days"] is None
    assert st.status()["last_siren_test"]


async def test_time_alone_makes_a_test_overdue(hass, freezer):
    hass.states.async_set("switch.siren", "off")
    m, entry, st = await _ready(hass, freezer)
    freezer.tick(timedelta(days=31))
    await st._tick()  # first reminder
    await hass.async_block_till_done()
    assert "selftest_overdue" not in issues(hass)
    freezer.tick(timedelta(days=8))
    await st._tick()  # after the second reminder there is no event any more, only time
    freezer.tick(timedelta(days=1))
    await st._tick()
    await hass.async_block_till_done()
    assert "selftest_overdue" in issues(hass)


async def test_the_overdue_repair_appears_and_goes_away(hass, freezer):
    hass.states.async_set("switch.siren", "off")
    m, entry, st = await _ready(hass, freezer)
    freezer.tick(timedelta(days=40))
    await st._tick()
    await hass.async_block_till_done()
    assert "selftest_overdue" in issues(hass)
    await hass.services.async_call("vigil_alarm", "test_siren", {"duration": 2}, blocking=True)
    await hass.async_block_till_done()
    assert "selftest_overdue" not in issues(hass)


async def test_no_reminder_in_the_middle_of_the_night(hass, freezer):
    hass.states.async_set("switch.siren", "off")
    m, entry, st = await _ready(hass, freezer, NIGHT_PACIFIC)
    freezer.tick(timedelta(days=31))
    await st._tick()
    assert not [x for x in sent(m) if "test" in x.lower() and "alarm" in x.lower()]


async def test_the_siren_can_sound_by_itself_when_turned_on(hass, freezer):
    hass.states.async_set("switch.siren", "off")
    m, entry, st = await _ready(hass, freezer, selftest_auto=True)
    freezer.tick(timedelta(days=31))
    await st._tick()
    assert len(m.on) == 1 and sent(m) == []
    assert st.status()["last_siren_test"] and st.status()["auto"] is True


async def test_a_button_in_the_message_sounds_the_siren(hass, freezer):
    hass.states.async_set("switch.siren", "off")
    m, entry, st = await _ready(hass, freezer)
    hass.bus.async_fire("mobile_app_notification_action", {"action": "VIGIL_TEST_SIREN"})
    await hass.async_block_till_done()
    assert len(m.on) == 1 and st.status()["last_siren_test"]
    hass.bus.async_fire("mobile_app_notification_action", {"action": "SOMETHING_ELSE"})
    await hass.async_block_till_done()
    assert len(m.on) == 1


async def test_reminders_can_be_turned_off(hass, freezer):
    hass.states.async_set("switch.siren", "off")
    m, entry, st = await _ready(hass, freezer, selftest_interval_days=0)
    freezer.tick(timedelta(days=100))
    await st._tick()
    assert st.status()["enabled"] is False and st.status()["due"] is None
    assert not any("test" in x.lower() and "siren" in x.lower() for x in sent(m))


async def test_selftest_settings_have_limits(hass, hass_ws_client):
    from .test_panel import _client

    entry, client = await _client(hass, hass_ws_client)
    snap = (await _ws(client, type="vigil_alarm/get"))["result"]["entry"]["data"]
    assert snap["selftest_interval_days"] == 30 and snap["selftest_siren_seconds"] == 2 and snap["selftest_auto"] is False
    bad = await _ws(client, type="vigil_alarm/save_settings", data={**snap, "selftest_siren_seconds": 9})
    assert bad["result"]["errors"] == {"selftest_siren_seconds": "selftest_range"}
    bad = await _ws(client, type="vigil_alarm/save_settings", data={**snap, "selftest_window_start": 20, "selftest_window_end": 9})
    assert bad["result"]["errors"] == {"selftest_window_end": "selftest_window"}
    ok = await _ws(client, type="vigil_alarm/save_settings", data={**snap, "selftest_interval_days": 14})
    assert ok["result"]["ok"] is True
    status = (await _ws(client, type="vigil_alarm/selftest"))["result"]
    assert {"last_check", "last_siren_test", "due", "overdue_days", "enabled", "siren"} <= set(status)


async def test_settings_form_is_in_sections_and_hidden_hours_are_kept(hass, hass_ws_client):
    from .test_panel import _client

    entry, client = await _client(hass, hass_ws_client)
    form = (await _ws(client, type="vigil_alarm/get"))["result"]["settings_form"]
    assert all(f.get("section") for f in form)
    assert {f["section"] for f in form} == {"alarm", "startup", "codes", "lock", "screen", "battery", "log", "selftest", "heartbeat"}
    snap = (await _ws(client, type="vigil_alarm/get"))["result"]["entry"]["data"]
    await _ws(client, type="vigil_alarm/save_settings", data={**snap, "selftest_window_start": 7, "selftest_window_end": 18})
    await hass.async_block_till_done()
    hidden = {k: v for k, v in snap.items() if not k.startswith("selftest_window")}  # the panel omits them while auto is off
    ok = await _ws(client, type="vigil_alarm/save_settings", data={**hidden, "selftest_interval_days": 14})
    assert ok["result"]["ok"] is True
    data = (await _ws(client, type="vigil_alarm/get"))["result"]["entry"]["data"]
    assert data["selftest_window_start"] == 7 and data["selftest_window_end"] == 18
