"""The register of panels: the profile, what a panel may do, unlocking, the lockout per panel and the offline report."""

from __future__ import annotations

from datetime import timedelta

import pytest
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import issue_registry as ir
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import MockConfigEntry, async_fire_time_changed, async_mock_service

from custom_components.vigil_alarm.const import DOMAIN, PANEL_OFFLINE_SECONDS
from custom_components.vigil_alarm.credentials import hash_code
from custom_components.vigil_alarm.manager import VigilManager

from .common import EVENTS, PANEL, make_entry, sub, plain
from .test_control_points import _vigil
from .test_integration import _setup


def panel_item(pid="garage", name="Garage panel", sid="p_garage", admin_code="9999", **data):
    body = {"panel_id": pid, "language": "", "allowed_modes": [], "can_disarm": True, "can_bypass": True,
            "can_silence": True, "sensor_list": "code", "unlock_seconds": 60, "blocked": False, **data}
    if admin_code:
        body["code_hash"], body["code_salt"] = hash_code(admin_code)
    return sub("panel", name, body, sid)


async def _house(hass, *panels, **data):
    return await _setup(hass, make_entry(extra_subentries=list(panels), **data))


def profile(hass, entity="sensor.garage_profile"):
    state = hass.states.get(entity)
    assert state is not None, [s.entity_id for s in hass.states.async_all() if "profile" in s.entity_id]
    return state


async def test_a_registered_panel_gets_a_profile_without_sensor_names_or_secrets(hass):
    await _house(hass, panel_item())
    state = profile(hass)
    a = state.attributes
    assert state.state == "1" and a["profile_version"] == 1 and a["panel_id"] == "garage"
    assert a["allowed_modes"] == ["home", "away", "night"] and a["can_disarm"] and a["sensor_list"] == "code"
    assert a["unlocked"] is False and a["sensors"] == "" and a["open_now_text"] == ""
    assert a["has_admin_code"] is True and a["code_arm_required"] is True and a["alarm"] == [PANEL]
    text = str(dict(a))
    assert "code_hash" not in text and "salt" not in text and "9999" not in text and "Front door" not in text


async def test_the_profile_attributes_with_names_are_kept_out_of_the_recorder(hass):
    from custom_components.vigil_alarm.alarm_control_panel import VigilAlarmPanel
    from custom_components.vigil_alarm.sensor import VigilPanelProfile

    assert {"sensors", "unlocked", "open_now_text", "open_sensors_text", "faults_text"} <= VigilPanelProfile._unrecorded_attributes
    # nothing with sensor names is left on the alarm entity for the recorder to keep
    assert not {"panel_sensors", "open_now_text", "open_sensors_text", "faults_text"} & set(VigilAlarmPanel._unrecorded_attributes)


async def test_unlocking_with_a_user_code_puts_the_user_in_the_event_and_the_log(hass):
    entry = await _house(hass, panel_item(unlock_seconds=30))
    manager = entry.runtime_data
    await manager.panels.async_unlock_with_code("1234", "garage", "sensors")  # Anna's code
    await hass.async_block_till_done()
    logged = [e for e in manager.eventlog.entries if e["event"] == "panel_unlocked"]
    assert logged and logged[-1]["user"] == "Anna" and logged[-1]["source"] == "garage"


async def test_unlocking_shows_the_sensors_for_a_while_and_then_hides_them_again(hass, freezer):
    entry = await _house(hass, panel_item(unlock_seconds=30))
    hass.states.async_set("binary_sensor.front_door", "on")
    await hass.async_block_till_done()
    panels = entry.runtime_data.panels
    item = panels.get("garage")
    panels.unlock(item, by="Admin")
    await hass.async_block_till_done()
    a = profile(hass).attributes
    assert a["unlocked"] is True and "Front door" in a["sensors"] and a["open_count"] >= 1
    assert hass.states.get(EVENTS).attributes["event_type"] == "panel_unlocked"
    freezer.tick(timedelta(seconds=31))
    async_fire_time_changed(hass, dt_util.utcnow())
    await hass.async_block_till_done()
    a = profile(hass).attributes
    assert a["unlocked"] is False and a["sensors"] == ""


async def test_the_sensor_list_setting_decides_what_the_profile_shows(hass):
    entry = await _house(hass, panel_item(pid="always", name="Always panel", sid="p1", sensor_list="always"),
                         panel_item(pid="never", name="Never panel", sid="p2", sensor_list="never"))
    never = entry.runtime_data.panels.get("never")
    entry.runtime_data.panels.unlock(never)  # even unlocked, "never" shows nothing
    await hass.async_block_till_done()
    assert "Front door" in profile(hass, "sensor.always_profile").attributes["sensors"]
    assert profile(hass, "sensor.never_profile").attributes["sensors"] == ""


async def test_unlock_with_the_administrator_code_of_the_panel(hass):
    await _house(hass, panel_item())
    await hass.services.async_call(DOMAIN, "unlock_panel", {"code": "9999", "source": "garage"}, blocking=True)
    assert profile(hass).attributes["unlocked"] is True
    with pytest.raises(ServiceValidationError, match="not a registered panel"):
        await hass.services.async_call(DOMAIN, "unlock_panel", {"code": "9999", "source": "phone"}, blocking=True)


async def test_a_user_code_does_not_unlock_and_wrong_admin_codes_lock_only_that_timer(hass, monkeypatch):
    entry = await _house(hass, panel_item(), panel_item(pid="hall", name="Hall panel", sid="p_hall"))
    clock = [1000.0]
    monkeypatch.setattr(VigilManager, "_clock", staticmethod(lambda: clock[0]))
    for _ in range(3):
        with pytest.raises(ServiceValidationError, match="Invalid code|Too many wrong codes"):
            await hass.services.async_call(DOMAIN, "unlock_panel", {"code": "1234", "source": "garage"}, blocking=True)
    with pytest.raises(ServiceValidationError, match="Too many wrong codes"):
        await hass.services.async_call(DOMAIN, "unlock_panel", {"code": "9999", "source": "garage"}, blocking=True)
    # the user-code timer of the same panel and the other panel are not affected
    await _vigil(hass, "arm", mode="home", code="1234", source="garage")
    await hass.services.async_call(DOMAIN, "unlock_panel", {"code": "9999", "source": "hall"}, blocking=True)
    assert entry.runtime_data.lockout.status() == {"admin:garage": 300.0}


async def test_a_panel_without_an_administrator_code_cannot_unlock_by_code(hass):
    await _house(hass, panel_item(admin_code=None))
    with pytest.raises(ServiceValidationError, match="no installer code"):
        await hass.services.async_call(DOMAIN, "unlock_panel", {"code": "1234", "source": "garage"}, blocking=True)


async def test_the_profile_limits_what_a_panel_may_do_and_every_refusal_is_logged(hass):
    await _house(hass, panel_item(allowed_modes=["home"], can_silence=False, can_disarm=False))
    await _vigil(hass, "arm", mode="home", code="1234", source="garage")
    for call, args, action in (
        ("arm", {"mode": "away", "code": "1234"}, "arm"),
        ("disarm", {"code": "1234"}, "disarm"),
        ("silence", {"code": "1234"}, "silence"),
    ):
        with pytest.raises(ServiceValidationError, match="may not do this"):
            await _vigil(hass, call, source="garage", **args)
        attrs = hass.states.get(EVENTS).attributes
        assert attrs["event_type"] == "panel_refused" and attrs["action"] == action and attrs["source"] == "garage"
    assert hass.states.get(PANEL).state == "armed_home"
    await _vigil(hass, "disarm", code="1234", source="phone")  # an unregistered source is not restricted
    assert hass.states.get(PANEL).state == "disarmed"


async def test_bypass_from_a_panel_always_needs_a_code(hass):
    await _house(hass, panel_item(), code_arm_required=False)
    await hass.services.async_call(DOMAIN, "bypass", {"sensor": "binary_sensor.living_pir", "source": "phone"}, blocking=True)
    with pytest.raises(ServiceValidationError, match="code is required"):
        await hass.services.async_call(DOMAIN, "bypass", {"sensor": "binary_sensor.front_door", "source": "garage"}, blocking=True)


async def test_a_blocked_panel_is_refused_before_any_code_is_looked_at(hass):
    entry = await _house(hass, panel_item(blocked=True))
    with pytest.raises(ServiceValidationError, match="is blocked"):
        await _vigil(hass, "disarm", code="0000", source="garage")  # a wrong code is not even counted
    assert hass.states.get(EVENTS).attributes["reason"] == "blocked"
    assert entry.runtime_data.lockout.status() == {}
    a = profile(hass).attributes
    assert a["blocked"] is True and a["allowed_modes"] == [] and not a["can_disarm"] and a["sensors"] == ""
    with pytest.raises(ServiceValidationError, match="is blocked"):
        entry.runtime_data.panels.unlock(entry.runtime_data.panels.get("garage"))


async def test_every_registered_panel_has_its_own_lockout_timer(hass, monkeypatch):
    entry = await _house(hass, panel_item(), panel_item(pid="hall", name="Hall panel", sid="p_hall"))
    clock = [1000.0]
    monkeypatch.setattr(VigilManager, "_clock", staticmethod(lambda: clock[0]))
    for _ in range(3):
        with pytest.raises(ServiceValidationError, match="Invalid code|Too many wrong codes"):
            await _vigil(hass, "disarm", code="0000", source="garage")
    with pytest.raises(ServiceValidationError, match="Too many wrong codes"):
        await _vigil(hass, "arm", mode="home", code="1234", source="garage")
    await _vigil(hass, "arm", mode="home", code="1234", source="hall")  # the other panel still works
    await _vigil(hass, "disarm", code="1234", source="phone")  # and so does everything else
    assert set(entry.runtime_data.lockout.status()) == {"garage"}


async def test_clearing_the_lock_lifts_both_timers_and_is_logged(hass, monkeypatch):
    entry = await _house(hass, panel_item())
    clock = [1000.0]
    monkeypatch.setattr(VigilManager, "_clock", staticmethod(lambda: clock[0]))
    for _ in range(3):
        with pytest.raises(ServiceValidationError):
            await _vigil(hass, "disarm", code="0000", source="garage")
    panels = entry.runtime_data.panels
    assert panels.status()[0]["locked_for"] > 0
    assert panels.clear_lock(panels.get("garage"), by="Admin") is True
    assert panels.status()[0]["locked_for"] == 0
    attrs = hass.states.get(EVENTS).attributes
    assert attrs["event_type"] == "panel_lock_cleared" and attrs["by"] == "Admin"
    await _vigil(hass, "arm", mode="home", code="1234", source="garage")
    assert panels.clear_lock(panels.get("garage")) is False


def _esphome(hass, name="garage", available=True):
    cfg = MockConfigEntry(domain="esphome", data={"device_name": name}, title=name)
    cfg.add_to_hass(hass)
    from homeassistant.helpers import entity_registry as er

    reg = er.async_get(hass)
    ent = reg.async_get_or_create("sensor", "esphome", f"{name}_wifi", config_entry=cfg, suggested_object_id=f"{name}_wifi")
    hass.states.async_set(ent.entity_id, "-50" if available else "unavailable")
    return ent.entity_id


async def test_a_panel_that_is_out_of_reach_for_ten_minutes_gives_a_repair_and_a_message(hass, freezer):
    calls = async_mock_service(hass, "notify", "mobile_app_anna")
    entity = _esphome(hass, available=False)
    from .test_notifications import channel

    entry = await _house(hass, panel_item(), channel(categories=("fault",)))
    await hass.async_block_till_done()
    assert not ir.async_get(hass).issues  # not yet
    freezer.tick(timedelta(seconds=PANEL_OFFLINE_SECONDS - 60))
    async_fire_time_changed(hass, dt_util.utcnow())
    await hass.async_block_till_done()
    assert not [i for i in ir.async_get(hass).issues if "panel_offline" in i[1]]
    freezer.tick(timedelta(seconds=120))
    async_fire_time_changed(hass, dt_util.utcnow())
    await hass.async_block_till_done()
    assert [i for i in ir.async_get(hass).issues if "panel_offline" in i[1]]
    assert [c.data["message"] for c in calls] == ["Panel not reachable for 10 minutes: Garage panel"]
    assert entry.runtime_data.panels.status()[0]["offline"] is True
    hass.states.async_set(entity, "-48")  # back
    freezer.tick(timedelta(seconds=31))
    async_fire_time_changed(hass, dt_util.utcnow())
    await hass.async_block_till_done()
    assert not [i for i in ir.async_get(hass).issues if "panel_offline" in i[1]]
    assert calls[-1].data["message"] == "Panel reachable again: Garage panel"
    assert hass.states.get(PANEL).state == "disarmed"  # an offline panel never changes the alarm


async def test_a_blocked_panel_gives_no_repair_when_it_is_out_of_reach(hass, freezer):
    _esphome(hass, available=False)
    await _house(hass, panel_item(blocked=True))
    freezer.tick(timedelta(seconds=PANEL_OFFLINE_SECONDS + 60))
    async_fire_time_changed(hass, dt_util.utcnow())
    await hass.async_block_till_done()
    assert not [i for i in ir.async_get(hass).issues if "panel_offline" in i[1]]


async def test_a_panel_that_is_not_watched_gives_no_repair_and_no_message(hass, freezer):
    calls = async_mock_service(hass, "notify", "mobile_app_anna")
    _esphome(hass, available=False)
    from .test_notifications import channel

    entry = await _house(hass, panel_item(watch=False), channel(categories=("fault",)))
    freezer.tick(timedelta(seconds=PANEL_OFFLINE_SECONDS + 600))
    async_fire_time_changed(hass, dt_util.utcnow())
    await hass.async_block_till_done()
    assert not [i for i in ir.async_get(hass).issues if "panel_offline" in i[1]]
    assert calls == []
    status = entry.runtime_data.panels.status()[0]
    assert status["watched"] is False and status["offline"] is False


async def test_a_register_entry_from_before_the_setting_is_still_watched(hass, freezer):
    # panel_item() has no `watch` at all, like an entry saved by an older version
    _esphome(hass, available=False)
    entry = await _house(hass, panel_item())
    assert "watch" not in next(iter(entry.runtime_data.panels.items())).data
    freezer.tick(timedelta(seconds=PANEL_OFFLINE_SECONDS + 60))
    async_fire_time_changed(hass, dt_util.utcnow())
    await hass.async_block_till_done()
    assert [i for i in ir.async_get(hass).issues if "panel_offline" in i[1]]
    assert entry.runtime_data.panels.status()[0]["watched"] is True


async def test_the_watch_choice_is_saved_and_offered_in_the_form(hass, hass_ws_client):
    from custom_components.vigil_alarm.items import items_of

    entry, client = await _client(hass, hass_ws_client)
    await _ws(client, type="vigil_alarm/save", kind="panel", data={"name": "Hall", "panel_id": "hall", "watch": False})
    await _ws(client, type="vigil_alarm/save", kind="panel", data={"name": "Gar", "panel_id": "gar"})
    await hass.async_block_till_done()
    panels = {i.data["panel_id"]: i for i in items_of(entry).values() if i.subentry_type == "panel"}
    assert panels["hall"].data["watch"] is False and panels["gar"].data["watch"] is True
    form = (await _ws(client, type="vigil_alarm/get"))["result"]["forms"]["panel"]
    field = next(f for f in form if f["key"] == "watch")
    assert field["type"] == "boolean" and field["default"] is True


async def _client(hass, hass_ws_client, *panels):
    entry = await _house(hass, *panels)
    return entry, await hass_ws_client(hass)


async def _ws(client, **msg):
    await client.send_json_auto_id(msg)
    return await client.receive_json()


async def test_the_admin_panel_registers_a_panel_and_checks_the_input(hass, hass_ws_client):
    from custom_components.vigil_alarm.items import items_of

    entry, client = await _client(hass, hass_ws_client)
    ok = await _ws(client, type="vigil_alarm/save", kind="panel",
                   data={"name": "Hall", "panel_id": "hall", "code": "4321", "allowed_modes": ["home", "away", "night"]})
    assert ok["result"]["ok"] is True
    await hass.async_block_till_done()
    item = next(i for i in items_of(entry).values() if i.subentry_type == "panel")
    assert item.data["panel_id"] == "hall" and item.data["allowed_modes"] == []  # all modes = "all"
    assert item.data["sensor_list"] == "code" and item.data["unlock_seconds"] == 60 and item.data["can_disarm"] is True
    assert "4321" not in plain(item.data) and item.data["code_hash"]
    got = (await _ws(client, type="vigil_alarm/get"))["result"]
    listed = got["items"]["panel"][0]
    assert listed["has_code"] is True and "code_hash" not in listed["data"] and "code_salt" not in listed["data"]
    assert [f["key"] for f in got["forms"]["panel"]][:3] == ["name", "device", "panel_id"]
    for data, errors in (
        ({"name": "X", "panel_id": "Bad Id"}, {"panel_id": "panel_id_invalid"}),
        ({"name": "X", "panel_id": "hall"}, {"panel_id": "panel_id_in_use"}),
        ({"name": "Hall", "panel_id": "other"}, {"name": "name_in_use"}),
        ({"name": "X", "panel_id": "x1", "unlock_seconds": 5}, {"unlock_seconds": "unlock_range"}),
        ({"name": "X", "panel_id": "x1", "sensor_list": "sometimes"}, {"sensor_list": "unknown_choice"}),
        ({"name": "X", "panel_id": "x1", "code": "12"}, {"code": "code_too_short"}),
    ):
        res = await _ws(client, type="vigil_alarm/save", kind="panel", data=data)
        assert res["result"]["ok"] is False and res["result"]["errors"] == errors, (data, res)


async def test_editing_a_panel_keeps_its_code_unless_asked_otherwise(hass, hass_ws_client):
    from custom_components.vigil_alarm.items import items_of

    entry, client = await _client(hass, hass_ws_client, panel_item())
    before = items_of(entry)["p_garage"].data["code_hash"]
    await _ws(client, type="vigil_alarm/save", kind="panel", subentry_id="p_garage",
              data={"name": "Garage panel", "panel_id": "garage", "blocked": True})
    await hass.async_block_till_done()
    assert items_of(entry)["p_garage"].data["code_hash"] == before and items_of(entry)["p_garage"].data["blocked"] is True
    await _ws(client, type="vigil_alarm/save", kind="panel", subentry_id="p_garage",
              data={"name": "Garage panel", "panel_id": "garage", "remove_code": True})
    await hass.async_block_till_done()
    assert "code_hash" not in items_of(entry)["p_garage"].data


async def test_unlock_and_clear_lock_exist_only_as_admin_commands_and_are_logged_with_the_admin(hass, hass_ws_client):
    entry, client = await _client(hass, hass_ws_client, panel_item())
    res = await _ws(client, type="vigil_alarm/panel_unlock", subentry_id="p_garage")
    assert res["success"] and res["result"]["ok"]
    await hass.async_block_till_done()
    assert profile(hass).attributes["unlocked"] is True
    assert hass.states.get(EVENTS).attributes["by"]
    res = await _ws(client, type="vigil_alarm/panel_clear_lock", subentry_id="p_garage")
    assert res["success"] and res["result"]["was_locked"] is False
    assert (await _ws(client, type="vigil_alarm/panel_unlock", subentry_id="nope"))["success"] is False
    assert not hass.services.has_service(DOMAIN, "panel_unlock") and not hass.services.has_service(DOMAIN, "clear_lock")
    live = entry.runtime_data.panels.status()
    assert live[0]["unlocked"] is True and live[0]["connected"] is None


async def test_a_blocked_panel_cannot_be_unlocked_from_the_admin_panel(hass, hass_ws_client):
    _, client = await _client(hass, hass_ws_client, panel_item(blocked=True))
    res = await _ws(client, type="vigil_alarm/panel_unlock", subentry_id="p_garage")
    assert res["success"] is False


async def test_a_removed_panel_takes_its_entity_with_it(hass, hass_ws_client):
    from homeassistant.helpers import entity_registry as er

    entry, client = await _client(hass, hass_ws_client, panel_item())
    assert er.async_get(hass).async_get_entity_id("sensor", DOMAIN, f"{entry.entry_id}_p_garage_profile")
    await _ws(client, type="vigil_alarm/delete", subentry_id="p_garage")
    await hass.async_block_till_done()
    assert not er.async_get(hass).async_get_entity_id("sensor", DOMAIN, f"{entry.entry_id}_p_garage_profile")


def _reports(hass, name="garage", **values):
    """The sensors a panel's firmware has for what it reports, by the names the firmware gives them."""
    from homeassistant.helpers import entity_registry as er

    cfg = next(c for c in hass.config_entries.async_entries("esphome") if c.data["device_name"] == name)
    reg = er.async_get(hass)
    names = {"hardware": "Hardware ID", "capabilities": "Capabilities", "firmware": "Firmware version",
             "profile_supported": "Profile version"}
    for key, value in values.items():
        ent = reg.async_get_or_create("sensor", "esphome", f"{name}_{key}", config_entry=cfg,
                                      original_name=names[key], suggested_object_id=f"{name}_{key}")
        hass.states.async_set(ent.entity_id, value)


async def test_what_the_panel_reports_about_itself_is_shown(hass):
    _esphome(hass)
    _reports(hass, hardware="guition-4848", capabilities="touch,screen", firmware="0.4.0", profile_supported="1")
    entry = await _house(hass, panel_item())
    status = entry.runtime_data.panels.status()[0]
    assert status["reported"] == {"hardware": "guition-4848", "capabilities": "touch,screen",
                                  "firmware": "0.4.0", "profile_supported": "1"}
    assert entry.runtime_data.panels.problems() == []


async def test_firmware_that_does_not_understand_the_profile_is_reported(hass):
    from custom_components.vigil_alarm.readiness import async_readiness

    _esphome(hass)
    _reports(hass, hardware="other-board", firmware="0.3.0", profile_supported="0")
    entry = await _house(hass, panel_item())
    problems = {p["code"]: p for p in entry.runtime_data.panels.problems()}
    assert problems["panel_firmware"]["seen"] == "0" and problems["panel_firmware"]["wanted"] == "1"
    assert "panel_hardware" not in problems
    findings = {f["code"]: f for f in async_readiness(hass, entry)}
    assert findings["panel_firmware"]["go"] == "panel"
    assert findings["panel_firmware"]["params"]["name"] == "Garage panel"


async def test_a_panel_that_reports_nothing_and_a_blocked_one_are_not_a_firmware_problem(hass):
    _esphome(hass)
    entry = await _house(hass, panel_item(), panel_item(pid="hall", name="Hall", sid="p2", blocked=True))
    assert entry.runtime_data.panels.problems() == []


async def test_the_profile_entity_has_an_id_that_follows_the_panel_id_not_the_name(hass):
    await _house(hass, panel_item(pid="vigil-panel-garage", name="Whatever name I like", sid="p9"))
    state = hass.states.get("sensor.vigil_panel_garage_profile")
    assert state is not None and state.attributes["panel_id"] == "vigil-panel-garage"
    assert state.attributes["friendly_name"] == "Whatever name I like profile"


async def test_a_profile_sensor_with_an_old_entity_id_is_renamed_to_follow_the_panel_id(hass):
    """An entity registry entry made by an earlier version keeps its id for ever, so Vigil renames it."""
    from homeassistant.helpers import entity_registry as er
    from pytest_homeassistant_custom_component.common import MockConfigEntry  # noqa: F401

    from .common import make_entry

    entry = make_entry(extra_subentries=[panel_item(pid="vigil-panel-garage", name="Garage", sid="p1")])
    entry.add_to_hass(hass)
    er.async_get(hass).async_get_or_create(
        "sensor", DOMAIN, f"{entry.entry_id}_p1_profile", suggested_object_id="garage_profile", config_entry=entry,
    )
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get("sensor.garage_profile") is None
    state = hass.states.get("sensor.vigil_panel_garage_profile")
    assert state is not None and state.attributes["panel_id"] == "vigil-panel-garage"


async def test_a_profile_sensor_whose_id_has_the_device_name_in_front_is_renamed(hass):
    """Newer Home Assistant versions can put the device name in front of an object id."""
    from homeassistant.helpers import entity_registry as er

    from .common import make_entry

    entry = make_entry(extra_subentries=[panel_item(pid="vigil-panel-garage", name="Panel garage", sid="p1")])
    entry.add_to_hass(hass)
    er.async_get(hass).async_get_or_create(
        "sensor", DOMAIN, f"{entry.entry_id}_p1_profile",
        suggested_object_id="panel_garage_vigil_panel_garage_profile", config_entry=entry,
    )
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get("sensor.vigil_panel_garage_profile") is not None
    assert hass.states.get("sensor.panel_garage_vigil_panel_garage_profile") is None


async def test_the_screen_settings_reach_the_panel_through_the_profile(hass):
    await _house(hass, panel_item())
    a = profile(hass).attributes
    assert a["screen_off_seconds"] == 30 and a["screen_off_on_alarm"] is False  # the defaults


async def test_the_screen_settings_are_saved_checked_and_follow_into_the_profile(hass, hass_ws_client):
    from .test_panel import _client as _plain_client, _ws

    entry, client = await _plain_client(hass, hass_ws_client, make_entry(extra_subentries=[panel_item()]))
    snap = (await _ws(client, type="vigil_alarm/get"))["result"]
    assert snap["entry"]["data"]["screen_off_seconds"] == 30 and snap["entry"]["data"]["screen_off_on_alarm"] is False
    keys = {f["key"] for f in snap["settings_form"]}
    assert {"screen_off_seconds", "screen_off_on_alarm"} <= keys
    data = dict(snap["entry"]["data"])
    for bad in (0, 4, 3601, "x"):
        res = await _ws(client, type="vigil_alarm/save_settings", data={**data, "screen_off_seconds": bad})
        assert res["result"]["errors"] == {"screen_off_seconds": "screen_off_range"}
    ok = await _ws(client, type="vigil_alarm/save_settings", data={**data, "screen_off_seconds": 90, "screen_off_on_alarm": True})
    assert ok["result"]["ok"] is True
    await hass.async_block_till_done()
    a = profile(hass).attributes
    assert a["screen_off_seconds"] == 90 and a["screen_off_on_alarm"] is True


async def test_a_panel_is_locked_for_good_after_the_last_step_and_only_clear_lock_opens_it(hass, monkeypatch):
    from homeassistant.helpers.dispatcher import async_dispatcher_connect
    from custom_components.vigil_alarm.manager import SIGNAL_EVENT

    entry = await _house(hass, panel_item())
    seen: list[str] = []
    async_dispatcher_connect(hass, SIGNAL_EVENT.format(entry.entry_id), lambda e: seen.append(e["type"]))
    clock = [1000.0]
    monkeypatch.setattr(VigilManager, "_clock", staticmethod(lambda: clock[0]))

    async def wrong(match="Invalid code"):
        with pytest.raises(ServiceValidationError, match=match):
            await _vigil(hass, "disarm", code="0000", source="garage")

    for tries, wait in ((3, 5), (2, 15), (2, 60)):
        for _ in range(tries - 1):
            await wrong()
        await wrong(f"Too many wrong codes. Try again in {wait} min")  # the wrong code that starts the lock says so
        with pytest.raises(ServiceValidationError, match=f"Try again in {wait} min"):
            await _vigil(hass, "arm", mode="home", code="1234", source="garage")
        clock[0] += 60  # a minute later the rest of the wait is still said, rounded up
        with pytest.raises(ServiceValidationError, match=f"Try again in {wait - 1} min"):
            await _vigil(hass, "arm", mode="home", code="1234", source="garage")
        clock[0] += wait * 60 - 60 + 1
    await wrong("until an administrator unlocks")  # the one wrong code of the last step
    await hass.async_block_till_done()
    assert "code_locked_permanent" in seen, seen
    assert entry.runtime_data.lockout.permanent() == {"garage"}
    clock[0] += 30 * 24 * 3600
    with pytest.raises(ServiceValidationError, match="until an administrator unlocks"):
        await _vigil(hass, "arm", mode="home", code="1234", source="garage")  # even the right code, even much later
    assert entry.runtime_data.panels.status()[0]["locked_permanent"] is True
    await _vigil(hass, "arm", mode="home", code="1234", source="hall")  # other callers are not affected
    panel = entry.runtime_data.panels.items()[0]
    assert entry.runtime_data.panels.clear_lock(panel, by="Admin") is True
    assert entry.runtime_data.panels.status()[0]["locked_permanent"] is False
    await _vigil(hass, "disarm", code="1234", source="garage")


async def test_the_locking_settings_are_saved_checked_and_used(hass, hass_ws_client, monkeypatch):
    from .test_panel import _client as _plain_client, _ws

    entry, client = await _plain_client(hass, hass_ws_client, make_entry(extra_subentries=[panel_item()]))
    snap = (await _ws(client, type="vigil_alarm/get"))["result"]
    data = dict(snap["entry"]["data"])
    assert [data[k] for k in ("lock_tries_1", "lock_wait_1", "lock_tries_2", "lock_wait_2", "lock_tries_3", "lock_wait_3", "lock_tries_4")] == [3, 5, 2, 15, 2, 60, 1]
    assert {f["key"] for f in snap["settings_form"] if f["section"] == "lock"} == {
        "lock_tries_1", "lock_wait_1", "lock_tries_2", "lock_wait_2", "lock_tries_3", "lock_wait_3", "lock_tries_4"}
    for key, bad, error in (("lock_tries_1", 0, "lock_tries_range"), ("lock_tries_4", 11, "lock_tries_range"),
                            ("lock_wait_2", 0, "lock_wait_range"), ("lock_wait_3", 1441, "lock_wait_range"), ("lock_wait_1", "x", "lock_wait_range")):
        res = await _ws(client, type="vigil_alarm/save_settings", data={**data, key: bad})
        assert res["result"]["errors"] == {key: error}
    ok = await _ws(client, type="vigil_alarm/save_settings", data={**data, "lock_tries_1": 1, "lock_wait_1": 2})
    assert ok["result"]["ok"] is True
    await hass.async_block_till_done()
    clock = [1000.0]
    monkeypatch.setattr(VigilManager, "_clock", staticmethod(lambda: clock[0]))
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    with pytest.raises(ServiceValidationError, match="Invalid code|Too many wrong codes"):
        await _vigil(hass, "disarm", code="0000", source="garage")  # one wrong code is enough now
    assert entry.runtime_data.lockout.remaining("garage") == 120


async def _unlock(hass, code, scope=None, source="garage"):
    data = {"code": code, "source": source, **({"scope": scope} if scope else {})}
    await hass.services.async_call(DOMAIN, "unlock_panel", data, blocking=True)


async def test_the_sensor_list_opens_with_a_user_code_but_the_info_needs_the_installer_code(hass):
    entry = await _house(hass, panel_item())
    panels = entry.runtime_data.panels
    await _unlock(hass, "1234", "sensors")  # Anna, a Vigil user
    await hass.async_block_till_done()
    assert panels.unlocked("garage") and profile(hass).attributes["unlocked"] is True
    panels.lock("garage")
    await _unlock(hass, "9999", "sensors")  # the installer code works for the list too
    assert panels.unlocked("garage")
    panels.lock("garage")
    for scope in (None, "info"):  # the info (and an old firmware without a scope) wants the installer code only
        with pytest.raises(ServiceValidationError, match="Invalid code"):
            await _unlock(hass, "1234", scope)
    assert not panels.unlocked("garage")
    await _unlock(hass, "9999", "info")
    assert panels.unlocked("garage")


async def test_wrong_codes_for_the_list_count_on_the_user_code_timer_and_a_right_one_resets(hass, monkeypatch):
    entry = await _house(hass, panel_item())
    clock = [1000.0]
    monkeypatch.setattr(VigilManager, "_clock", staticmethod(lambda: clock[0]))
    for _ in range(2):
        with pytest.raises(ServiceValidationError, match="Invalid code|Too many wrong codes"):
            await _unlock(hass, "0000", "sensors")
    await _unlock(hass, "1234", "sensors")  # a right code: the count starts again
    for _ in range(2):
        with pytest.raises(ServiceValidationError, match="Invalid code|Too many wrong codes"):
            await _unlock(hass, "0000", "sensors")
    with pytest.raises(ServiceValidationError, match="Invalid code|Too many wrong codes"):
        await _unlock(hass, "0000", "sensors")  # the third in a row
    assert set(entry.runtime_data.lockout.status()) == {"garage"}
    with pytest.raises(ServiceValidationError, match="Too many wrong codes"):
        await _unlock(hass, "1234", "sensors")


async def test_the_list_without_any_user_or_installer_code_says_so(hass):
    await _house(hass, panel_item(admin_code=None), users=False)
    with pytest.raises(ServiceValidationError, match="no installer code"):
        await _unlock(hass, "1234", "sensors")


async def test_only_a_user_with_the_right_may_bypass_a_sensor(hass):
    from .common import user_data

    entry = await _house(
        hass, panel_item(),
        sub("user", "Cleo", user_data("2468", may_bypass=True), "cleo"),
        sub("user", "Dave", user_data("1357", may_bypass=False), "dave"),
    )
    pir = {"sensor": "binary_sensor.living_pir", "source": "garage"}
    with pytest.raises(ServiceValidationError, match="right to bypass"):
        await _vigil(hass, "bypass", code="1357", **pir)  # Dave has a right code but not the right
    assert hass.states.get(PANEL).attributes["bypassed_sensors"] == []
    await _vigil(hass, "bypass", code="2468", **pir)  # Cleo may
    assert "Living PIR" in hass.states.get(PANEL).attributes["bypassed_sensors"]
    with pytest.raises(ServiceValidationError, match="right to bypass"):
        await _vigil(hass, "unbypass", code="1357", **pir)  # restoring follows the same rule as bypassing
    assert "Living PIR" in hass.states.get(PANEL).attributes["bypassed_sensors"]
    await _vigil(hass, "unbypass", code="2468", **pir)
    assert hass.states.get(PANEL).attributes["bypassed_sensors"] == []
    await _vigil(hass, "bypass", code="1234", **pir)  # Anna, saved without the right, keeps it until it is unticked
    tamper = {"sensor": "binary_sensor.tamper", "source": "garage"}
    with pytest.raises(ServiceValidationError, match="tamper"):
        await _vigil(hass, "bypass", code="2468", **tamper)  # Cleo may bypass, but not tamper
    with pytest.raises(ServiceValidationError, match="tamper"):
        await _vigil(hass, "unbypass", code="2468", **tamper)  # and so she cannot restore it either
    assert entry.runtime_data.lockout.status() == {}


async def test_the_bypass_right_is_a_field_of_the_user_and_old_users_keep_it(hass, hass_ws_client):
    from .test_panel import _client as _plain_client, _ws

    entry, client = await _plain_client(hass, hass_ws_client, make_entry(extra_subentries=[panel_item()]))
    snap = (await _ws(client, type="vigil_alarm/get"))["result"]
    fields = {f["key"]: f for f in snap["forms"]["user"]}
    assert fields["may_bypass"]["default"] is False and fields["may_bypass_tamper"]["show_if"] == {"may_bypass": [True]}
    anna = next(i for group in snap["items"].values() for i in group if i["title"] == "Anna")
    assert anna["data"]["may_bypass"] is True  # saved before the right existed
    res = await _ws(client, type="vigil_alarm/save", kind="user", data={"name": "Eve", "code": "86420", "may_bypass": True})
    assert res["result"].get("ok") is True
    await hass.async_block_till_done()
    from custom_components.vigil_alarm.items import items_of

    eve = next(i for i in items_of(entry).values() if i.title == "Eve")
    assert eve.data["may_bypass"] is True
    await _ws(client, type="vigil_alarm/save", kind="user", subentry_id=eve.subentry_id, data={"name": "Eve", "may_bypass": False})
    await hass.async_block_till_done()
    assert items_of(entry)[eve.subentry_id].data["may_bypass"] is False
