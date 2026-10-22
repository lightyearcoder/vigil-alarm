from __future__ import annotations

import pytest
from homeassistant.helpers import entity_registry as er

from custom_components.vigil_alarm.const import DOMAIN

from custom_components.vigil_alarm.items import items_of

from .common import make_entry, plain
from .test_integration import _setup


async def _client(hass, hass_ws_client, entry=None, **kw):
    entry = await _setup(hass, entry or make_entry(**kw))
    return entry, await hass_ws_client(hass)


async def _ws(client, **msg):
    await client.send_json_auto_id(msg)
    return await client.receive_json()


async def test_panel_is_registered_admin_only_and_removed_with_the_entry(hass):
    entry = await _setup(hass, make_entry())
    panels = hass.data["frontend_panels"]
    assert panels["vigil_alarm"].require_admin is True
    assert panels["vigil_alarm"].sidebar_title == "Vigil Alarm"
    await hass.config_entries.async_remove(entry.entry_id)
    await hass.async_block_till_done()
    assert "vigil_alarm" not in hass.data["frontend_panels"]


async def test_panel_stays_while_the_entry_reloads(hass):
    # Every save reloads the entry; the open panel must not vanish in between.
    entry = await _setup(hass, make_entry())
    assert await hass.config_entries.async_unload(entry.entry_id)
    assert "vigil_alarm" in hass.data["frontend_panels"]
    assert await hass.config_entries.async_setup(entry.entry_id)
    assert "vigil_alarm" in hass.data["frontend_panels"]


async def test_get_lists_everything_without_secrets(hass, hass_ws_client):
    entry, client = await _client(hass, hass_ws_client)
    res = await _ws(client, type="vigil_alarm/get")
    assert res["success"]
    result = res["result"]
    assert {z["title"] for z in result["items"]["sensor"]} == {"Front door", "Living PIR", "Smoke", "Tamper"}
    anna = next(u for u in result["items"]["user"] if u["title"] == "Anna")
    assert anna["has_code"] is True
    assert "code_hash" not in anna["data"] and "code_salt" not in anna["data"] and "1234" not in plain(result)
    assert "code_hash" not in str(result) and "code_salt" not in str(result)
    assert result["sensor_entities"]["front"]["bypass"] == "binary_sensor.front_door_bypassed"
    assert result["sensor_entities"]["front"]["status"] == "sensor.front_door_status"
    assert result["alarm_entity"] == "alarm_control_panel.vigil_alarm"
    assert [f["key"] for f in result["forms"]["sensor"]][:3] == ["name", "entity_id", "cls"]


async def test_everything_is_admin_only(hass, hass_ws_client, hass_read_only_access_token):
    await _setup(hass, make_entry())
    client = await hass_ws_client(hass, hass_read_only_access_token)
    for msg in (
        {"type": "vigil_alarm/get"},
        {"type": "vigil_alarm/about"},
        {"type": "vigil_alarm/subscribe"},
        {"type": "vigil_alarm/save", "kind": "sensor", "data": {"name": "x"}},
        {"type": "vigil_alarm/delete", "subentry_id": "front"},
        {"type": "vigil_alarm/save_settings", "data": {"modes": ["home"]}},
    ):
        res = await _ws(client, **msg)
        assert res["success"] is False and res["error"]["code"] == "unauthorized", msg


async def test_save_creates_and_updates_a_sensor(hass, hass_ws_client):
    entry, client = await _client(hass, hass_ws_client)
    sensor = {"name": "Garage PIR", "entity_id": "binary_sensor.garage", "cls": "intrusion", "type": "instant",
            "sensor_groups": ["g_away"], "at_arm_open": "wait_clear", "on_unavailable": "default"}
    res = await _ws(client, type="vigil_alarm/save", kind="sensor", data=sensor)
    assert res["result"]["ok"] is True
    new_id = res["result"]["id"]
    await hass.async_block_till_done()
    sub = items_of(entry)[new_id]
    assert sub.title == "Garage PIR" and sub.subentry_type == "zone" and "on_unavailable" not in sub.data
    assert hass.states.get("sensor.garage_pir_status") is not None  # the entry reloaded with the new sensor

    res = await _ws(client, type="vigil_alarm/save", kind="sensor", subentry_id=new_id, data={**sensor, "name": "Garage motion"})
    assert res["result"]["ok"] is True and res["result"]["id"] == new_id
    await hass.async_block_till_done()
    assert items_of(entry)[new_id].title == "Garage motion"


async def test_save_reports_errors_per_field(hass, hass_ws_client):
    entry, client = await _client(hass, hass_ws_client)
    base = {"name": "Dup", "entity_id": "binary_sensor.x", "cls": "intrusion", "type": "instant", "sensor_groups": ["g_away"]}
    res = await _ws(client, type="vigil_alarm/save", kind="sensor", data={**base, "name": "Front door"})
    assert res["result"] == {"ok": False, "errors": {"name": "name_in_use"}, "placeholders": {}}
    res = await _ws(client, type="vigil_alarm/save", kind="sensor", data={**base, "sensor_groups": []})
    assert res["result"]["errors"] == {"sensor_groups": "no_sensor_group"}
    res = await _ws(client, type="vigil_alarm/save", kind="sensor", data={**base, "sensor_groups": ["nope"]})
    assert res["result"]["errors"] == {"sensor_groups": "unknown_sensor_group"}
    res = await _ws(client, type="vigil_alarm/save", kind="sensor", data={**base, "name": " "})
    assert res["result"]["errors"] == {"name": "name_required"}
    # nothing was stored
    assert len(items_of(entry)) == 9


async def test_rule_with_a_delayed_sensor_is_refused_with_the_sensor_name(hass, hass_ws_client):
    entry, client = await _client(hass, hass_ws_client)
    res = await _ws(client, type="vigil_alarm/save", kind="rule", data={
        "name": "G", "sensors": ["front", "living"], "required": 2, "window": 60})
    assert res["result"]["errors"] == {"sensors": "sensor_not_instant"}
    assert res["result"]["placeholders"] == {"sensors": "Front door"}


async def test_user_codes_are_hashed_unique_and_kept_when_empty(hass, hass_ws_client):
    from custom_components.vigil_alarm.credentials import code_matches

    entry, client = await _client(hass, hass_ws_client)
    res = await _ws(client, type="vigil_alarm/save", kind="user", data={"name": "Carol", "code": "4321", "tags": [" t1 "]})
    cid = res["result"]["id"]
    carol = items_of(entry)[cid]
    assert code_matches("4321", carol.data) and "4321" not in plain(carol.data) and carol.data["tags"] == ["t1"]
    res = await _ws(client, type="vigil_alarm/save", kind="user", data={"name": "Dup", "code": "1234"})
    assert res["result"]["errors"] == {"code": "code_in_use"}
    res = await _ws(client, type="vigil_alarm/save", kind="user", subentry_id=cid, data={"name": "Carol B", "tags": ["t1"]})
    await hass.async_block_till_done()
    assert code_matches("4321", items_of(entry)[cid].data)  # empty code field = keep
    res = await _ws(client, type="vigil_alarm/save", kind="user", subentry_id=cid, data={"name": "Carol B", "tags": ["t1"], "remove_code": True})
    await hass.async_block_till_done()
    assert "code_hash" not in items_of(entry)[cid].data and items_of(entry)[cid].data["tags"] == ["t1"]
    res = await _ws(client, type="vigil_alarm/save", kind="user", subentry_id=cid, data={"name": "Carol B", "remove_code": True})
    assert res["result"]["errors"] == {"base": "no_credential"}  # removing the only credential is refused


async def test_notification_and_siren(hass, hass_ws_client):
    entry, client = await _client(hass, hass_ws_client)
    hass.services.async_register("notify", "phone", lambda call: None)
    res = await _ws(client, type="vigil_alarm/save", kind="notification", data={
        "name": "Phone", "service": "phone", "categories": ["alarm"], "delay": 0})
    assert res["result"]["ok"] is True
    res = await _ws(client, type="vigil_alarm/save", kind="notification", data={
        "name": "Ghost", "service": "nope", "categories": ["alarm"], "delay": 0})
    assert res["result"]["errors"] == {"services": "service_not_found"}
    res = await _ws(client, type="vigil_alarm/save", kind="siren", data={
        "name": "Hall", "control": "switch.siren", "causes": ["intrusion"], "intrusion": {"tone": "alarm_1"}})
    assert res["result"]["errors"] == {"base": "tone_without_entity"}
    res = await _ws(client, type="vigil_alarm/save", kind="siren", data={
        "name": "Hall", "control": "switch.siren", "causes": ["intrusion"], "max_duration": 120,
        "tone_entity": "select.tone", "intrusion": {"tone": "alarm_1", "volume": ""}})
    assert res["result"]["ok"] is True
    hall = next(s for s in items_of(entry).values() if s.title == "Hall")
    assert hall.data["intrusion"] == {"tone": "alarm_1"} and hall.data["max_duration"] == 120.0


async def test_delete(hass, hass_ws_client):
    entry, client = await _client(hass, hass_ws_client)
    res = await _ws(client, type="vigil_alarm/delete", subentry_id="bob")
    assert res["result"] == {"ok": True}
    await hass.async_block_till_done()
    assert "bob" not in items_of(entry)
    res = await _ws(client, type="vigil_alarm/delete", subentry_id="nope")
    assert res["success"] is False and res["error"]["code"] == "not_found"


async def test_a_sensor_in_a_rule_cannot_be_deleted(hass, hass_ws_client):
    from .common import sub

    rule = sub("group", "Down", {"sensors": ["living", "pir2"], "required": 2, "window": 60, "escalate": False}, "grp")
    pir2 = sub("zone", "PIR 2", {"entity_id": "binary_sensor.pir2", "cls": "intrusion", "type": "instant",
                                  "sensor_groups": ["g_away"], "at_arm_open": "wait_clear"}, "pir2")
    entry, client = await _client(hass, hass_ws_client, make_entry(extra_subentries=[pir2, rule]))
    res = await _ws(client, type="vigil_alarm/delete", subentry_id="living")
    assert res["result"] == {"ok": False, "errors": {"base": "sensor_in_rule"}, "placeholders": {"rules": "Down"}}
    assert "living" in items_of(entry)


async def test_settings(hass, hass_ws_client):
    entry, client = await _client(hass, hass_ws_client)
    data = dict(entry.data)
    res = await _ws(client, type="vigil_alarm/save_settings", data={**data, "exit_delay_away": 90, "bogus": 1})
    assert res["result"]["ok"] is True
    await hass.async_block_till_done()
    assert entry.data["exit_delay_away"] == 90 and "bogus" not in entry.data
    res = await _ws(client, type="vigil_alarm/save_settings", data={**data, "modes": []})
    assert res["result"]["errors"] == {"modes": "no_modes"}
    # Living PIR is only active in "away"; switching that mode off would leave it with no mode.
    res = await _ws(client, type="vigil_alarm/save_settings", data={**data, "modes": ["home", "night"]})
    assert res["result"]["errors"] == {"base": "invalid_config"}
    assert entry.data["modes"] == ["home", "away", "night"]


async def test_subscribe_pushes_live_state(hass, hass_ws_client):
    entry, client = await _client(hass, hass_ws_client)
    await client.send_json_auto_id({"type": "vigil_alarm/subscribe"})
    first = await client.receive_json()
    assert first["success"]
    event = await client.receive_json()
    assert event["event"]["state"] == "disarmed"
    assert event["event"]["sensors"]["front"] == "closed" and event["event"]["problems"] == []
    hass.states.async_set("binary_sensor.living_pir", "on")
    await hass.async_block_till_done()
    event = await client.receive_json()
    assert event["event"]["sensors"]["living"] == "open"


async def test_sensor_groups_in_the_panel(hass, hass_ws_client):
    entry, client = await _client(hass, hass_ws_client)
    res = await _ws(client, type="vigil_alarm/get")
    groups = {g["title"]: g["data"] for g in res["result"]["items"]["sensor_group"]}
    assert groups["Away only"] == {"modes": ["away"]}
    form = {f["key"]: f for f in res["result"]["forms"]["sensor_group"]}
    assert form["modes"]["options"] == ["home", "away", "night"] and form["suggest_for"]["options"] == ["", "contacts", "motion"]
    assert any(f["type"] == "sensor_groups" for f in res["result"]["forms"]["sensor"])
    assert not any(f["key"] == "modes" for f in res["result"]["forms"]["sensor"])

    res = await _ws(client, type="vigil_alarm/save", kind="sensor_group", data={"name": "Cellar", "modes": ["night", "home"]})
    assert res["result"]["ok"] is True
    cellar = items_of(entry)[res["result"]["id"]]
    assert cellar.subentry_type == "sensor_group" and cellar.data == {"modes": ["home", "night"]}
    res = await _ws(client, type="vigil_alarm/save", kind="sensor_group", data={"name": "Cellar", "modes": ["home"]})
    assert res["result"]["errors"] == {"name": "name_in_use"}
    res = await _ws(client, type="vigil_alarm/save", kind="sensor_group", data={"name": "Empty", "modes": []})
    assert res["result"]["errors"] == {"modes": "no_modes"}
    res = await _ws(client, type="vigil_alarm/save", kind="sensor_group", data={"name": "Odd", "modes": ["away"], "suggest_for": "x"})
    assert res["result"]["errors"] == {"suggest_for": "unknown_suggestion"}
    res = await _ws(client, type="vigil_alarm/save", kind="sensor_group", data={"name": "Odd", "modes": ["vacation"]})
    assert res["result"]["errors"] == {"modes": "no_modes"}
    res = await _ws(client, type="vigil_alarm/save", kind="sensor_group", data={"name": "Odd", "modes": ["away", "vacation"]})
    assert res["result"]["errors"] == {"modes": "unknown_mode"}


async def test_a_sensor_group_in_use_cannot_be_deleted_and_changes_the_watched_modes(hass, hass_ws_client):
    from custom_components.vigil_alarm.manager import build_config

    entry, client = await _client(hass, hass_ws_client)
    res = await _ws(client, type="vigil_alarm/delete", subentry_id="g_away")
    assert res["result"] == {"ok": False, "errors": {"base": "sensor_group_in_use"},
                             "placeholders": {"sensors": "Living PIR"}}
    assert "g_away" in items_of(entry)
    # an unused group can go
    res = await _ws(client, type="vigil_alarm/delete", subentry_id="g_home")
    assert res["result"] == {"ok": True}
    await hass.async_block_till_done()
    # changing a group changes where its sensors watch
    assert list(build_config(entry).sensors["living"].modes) == ["away"]
    res = await _ws(client, type="vigil_alarm/save", kind="sensor_group", subentry_id="g_away", data={"name": "Away only", "modes": ["away", "night"]})
    assert res["result"]["ok"] is True
    await hass.async_block_till_done()
    assert list(build_config(entry).sensors["living"].modes) == ["away", "night"]


async def test_channel_checks_the_service_and_names_are_unique(hass, hass_ws_client):
    entry, client = await _client(hass, hass_ws_client)
    hass.services.async_register("notify", "mobile_app_anna", lambda call: None)
    base = {"name": "Phone", "service": "mobile_app_anna", "categories": ["alarm"], "delay": 0, "priority": False}
    res = await _ws(client, type="vigil_alarm/save", kind="notification", data={**base, "categories": []})
    assert res["result"]["errors"] == {"categories": "no_categories"}
    res = await _ws(client, type="vigil_alarm/save", kind="notification", data=base)
    assert res["result"]["ok"] is True
    assert items_of(entry)[res["result"]["id"]].data["services"] == ["mobile_app_anna"]
    res = await _ws(client, type="vigil_alarm/save", kind="notification", data=base)
    assert res["result"]["errors"] == {"name": "name_in_use"}


async def test_siren_rules(hass, hass_ws_client):
    entry, client = await _client(hass, hass_ws_client)
    base = {"name": "Hall", "control": "switch.siren", "causes": ["fire"], "max_duration": 120, "repeat_every": 0,
            "intrusion": {}, "fire": {}, "gas": {}, "tamper": {}}
    res = await _ws(client, type="vigil_alarm/save", kind="siren", data={**base, "causes": []})
    assert res["result"]["errors"] == {"causes": "no_causes"}
    res = await _ws(client, type="vigil_alarm/save", kind="siren", data={**base, "fire": {"volume": "2"}})
    assert res["result"]["errors"] == {"base": "volume_without_entity"}
    res = await _ws(client, type="vigil_alarm/save", kind="siren", data={**base, "tone_entity": "select.t", "fire": {"tone": "alarm_fire", "volume": ""}})
    assert res["result"]["ok"] is True
    data = items_of(entry)[res["result"]["id"]].data
    assert data["fire"] == {"tone": "alarm_fire"} and "intrusion" not in data and "light" not in data
    res = await _ws(client, type="vigil_alarm/save", kind="siren", data=base)
    assert res["result"]["errors"] == {"name": "name_in_use"}


async def test_battery_and_power_fields_are_kept(hass, hass_ws_client):
    entry, client = await _client(hass, hass_ws_client)
    res = await _ws(client, type="vigil_alarm/save", kind="sensor", data={
        "name": "Bath PIR", "entity_id": "binary_sensor.bath", "cls": "intrusion", "type": "instant",
        "sensor_groups": ["g_away"], "battery_entity": "sensor.bath_battery"})
    assert items_of(entry)[res["result"]["id"]].data["battery_entity"] == "sensor.bath_battery"
    res = await _ws(client, type="vigil_alarm/save", kind="siren", data={
        "name": "Hall", "control": "switch.siren", "causes": ["fire"], "battery_entity": "sensor.siren_battery",
        "power_entity": "sensor.siren_power", "power_battery_value": "battery"})
    assert items_of(entry)[res["result"]["id"]].data["power_entity"] == "sensor.siren_power"


async def test_a_sensor_cannot_stop_being_instant_while_in_a_rule(hass, hass_ws_client):
    from .common import sub

    rule = sub("group", "Down", {"sensors": ["living", "pir2"], "required": 2, "window": 60, "escalate": False}, "grp")
    pir2 = sub("zone", "PIR 2", {"entity_id": "binary_sensor.pir2", "cls": "intrusion", "type": "instant",
                                  "sensor_groups": ["g_away"], "at_arm_open": "wait_clear"}, "pir2")
    entry, client = await _client(hass, hass_ws_client, make_entry(extra_subentries=[pir2, rule]))
    data = {"name": "PIR 2", "entity_id": "binary_sensor.pir2", "cls": "intrusion", "type": "delayed",
            "sensor_groups": ["g_away"], "at_arm_open": "wait_clear"}
    res = await _ws(client, type="vigil_alarm/save", kind="sensor", subentry_id="pir2", data=data)
    assert res["result"]["ok"] is False and res["result"]["errors"] == {"base": "invalid_config"}
    assert items_of(entry)["pir2"].data["type"] == "instant"


async def test_a_sensor_watches_in_the_modes_of_all_its_groups(hass, hass_ws_client):
    from custom_components.vigil_alarm.manager import build_config

    entry, client = await _client(hass, hass_ws_client)
    res = await _ws(client, type="vigil_alarm/save", kind="sensor", data={
        "name": "Hall PIR", "entity_id": "binary_sensor.hall", "cls": "intrusion", "type": "instant",
        "sensor_groups": ["g_home", "g_away"]})
    sid = res["result"]["id"]
    await hass.async_block_till_done()
    config = build_config(entry)
    assert list(config.sensors[sid].modes) == ["home", "away"]  # union, in the alarm's order
    assert list(config.sensors["front"].modes) == ["home", "away", "night"]


async def test_the_siren_preset_fills_values_and_finds_the_entities_of_the_same_device(hass, hass_ws_client):
    from homeassistant.helpers import device_registry as dr
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    entry, client = await _client(hass, hass_ws_client)
    other = MockConfigEntry(domain="mqtt")
    other.add_to_hass(hass)
    device = dr.async_get(hass).async_get_or_create(
        config_entry_id=other.entry_id, identifiers={("mqtt", "0x00124b0012345678")})
    registry = er.async_get(hass)
    ids = {}
    # an entity of another device must never be suggested (registered first, so a loose match would find it)
    registry.async_get_or_create("select", "mqtt", "0xffff_alarm_sound_type_zigbee2mqtt",
                                 suggested_object_id="other_tone")
    for domain, expose in (("switch", "siren_on"), ("switch", "alarm_light_enable"), ("select", "alarm_sound_type"),
                           ("select", "alarm_volume_level"), ("sensor", "battery"), ("sensor", "power_supply_mode"),
                           ("number", "alarm_duration")):
        ids[expose] = registry.async_get_or_create(
            domain, "mqtt", f"0x00124b0012345678_{expose}_zigbee2mqtt", suggested_object_id=f"hall_siren_{expose}",
            device_id=device.id).entity_id

    assert (await _ws(client, type="vigil_alarm/get"))["result"]["siren_presets"] == ["sonoff_snzb_09p_z2m"]
    res = await _ws(client, type="vigil_alarm/siren_preset", preset="sonoff_snzb_09p_z2m", control=ids["siren_on"])
    result = res["result"]
    assert result["values"]["tone_entity"] == ids["alarm_sound_type"]
    assert result["values"]["volume_entity"] == ids["alarm_volume_level"]
    assert result["values"]["light"] == ids["alarm_light_enable"]
    assert result["values"]["battery_entity"] == ids["battery"]
    assert result["values"]["power_entity"] == ids["power_supply_mode"]
    assert result["values"]["power_battery_value"] == "battery"
    assert result["values"]["fire"] == {"tone": "siren_warning", "volume": "max"}
    assert sorted(result["found"]) == ["battery_entity", "light", "power_entity", "tone_entity", "volume_entity"]

    # without a (known) control there are only values, no entities
    res = await _ws(client, type="vigil_alarm/siren_preset", preset="sonoff_snzb_09p_z2m")
    assert res["result"]["found"] == [] and "tone_entity" not in res["result"]["values"]
    res = await _ws(client, type="vigil_alarm/siren_preset", preset="nope")
    assert res["success"] is False and res["error"]["code"] == "not_found"

    # the preset values form a valid siren, and the helper field is never stored
    data = {"name": "Hall", "control": ids["siren_on"], "causes": ["intrusion", "fire"], "preset": "x", **result["values"]}
    res = await _ws(client, type="vigil_alarm/save", kind="siren", data=data)
    assert res["result"]["ok"] is True
    assert "preset" not in items_of(entry)[res["result"]["id"]].data


async def test_preset_command_is_admin_only(hass, hass_ws_client, hass_read_only_access_token):
    await _setup(hass, make_entry())
    client = await hass_ws_client(hass, hass_read_only_access_token)
    res = await _ws(client, type="vigil_alarm/siren_preset", preset="sonoff_snzb_09p_z2m")
    assert res["success"] is False and res["error"]["code"] == "unauthorized"


async def test_deleting_a_sensor_removes_its_entities_and_device(hass, hass_ws_client):
    from homeassistant.helpers import device_registry as dr

    entry, client = await _client(hass, hass_ws_client)
    assert hass.states.get("sensor.living_pir_status") is not None
    res = await _ws(client, type="vigil_alarm/delete", subentry_id="living")
    assert res["result"] == {"ok": True}
    await hass.async_block_till_done()
    assert hass.states.get("sensor.living_pir_status") is None
    assert er.async_get(hass).async_get("sensor.living_pir_status") is None
    names = {d.name for d in dr.async_entries_for_config_entry(dr.async_get(hass), entry.entry_id)}
    assert "Living PIR" not in names and "Front door" in names


async def test_the_minimum_code_length_is_a_setting_with_a_floor_of_four(hass, hass_ws_client):
    entry, client = await _client(hass, hass_ws_client)
    data = dict((await _ws(client, type="vigil_alarm/get"))["result"]["entry"]["data"])
    assert data["min_code_length"] == 4  # the default, also for entries saved before the setting existed
    res = await _ws(client, type="vigil_alarm/save", kind="user", data={"name": "Short", "code": "123"})
    assert res["result"]["errors"] == {"code": "code_too_short"} and res["result"]["placeholders"] == {"min": 4}
    for bad in (3, 13, "x"):
        res = await _ws(client, type="vigil_alarm/save_settings", data={**data, "min_code_length": bad})
        assert res["result"]["errors"] == {"min_code_length": "code_length_range"}
    res = await _ws(client, type="vigil_alarm/save_settings", data={**data, "min_code_length": 6})
    assert res["result"]["ok"] is True
    await hass.async_block_till_done()
    res = await _ws(client, type="vigil_alarm/save", kind="user", data={"name": "Mid", "code": "12345"})
    assert res["result"]["errors"] == {"code": "code_too_short"} and res["result"]["placeholders"] == {"min": 6}
    res = await _ws(client, type="vigil_alarm/save", kind="user", data={"name": "Ok", "code": "246810"})
    assert res["result"]["ok"] is True
