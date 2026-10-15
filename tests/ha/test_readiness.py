from __future__ import annotations

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.vigil_alarm.const import DOMAIN
from custom_components.vigil_alarm.items import items_of

from .common import make_entry, sub
from .test_discovery import _add, _device
from .test_integration import _setup
from .test_panel import _client, _ws


def _empty():
    base = make_entry()
    return MockConfigEntry(domain=DOMAIN, title=base.title, data=base.data, options={"items": {}},
                           unique_id=DOMAIN, version=3)


async def _codes(client):
    res = await _ws(client, type="vigil_alarm/readiness")
    assert res["success"]
    return {f["code"]: f for f in res["result"]["findings"]}


async def test_a_bare_installation_lists_what_is_missing(hass, hass_ws_client):
    entry, client = await _client(hass, hass_ws_client, users=False)
    found = await _codes(client)
    assert found["no_user_code"]["level"] == "problem" and found["no_user_code"]["go"] == "user"
    assert found["no_notification"]["go"] == "notification"
    assert found["no_siren"]["level"] == "advice"
    assert found["battery_missing"]["params"]["n"] == "3"


async def test_an_empty_alarm_asks_for_sensors_and_groups(hass, hass_ws_client):
    entry = _empty()
    entry, client = await _client(hass, hass_ws_client, entry)
    found = await _codes(client)
    assert found["no_sensors"]["go"] == "sensor"
    assert found["no_sensor_groups"]["go"] == "create_groups"


async def test_a_mode_nothing_watches_is_a_problem(hass, hass_ws_client):
    # make_entry's sensors are in "All modes" and "Away only": remove the night coverage.
    entry = make_entry()
    entry.options["items"]["g_all"]["data"]["modes"] = ["home", "away"]
    entry, client = await _client(hass, hass_ws_client, entry)
    found = await _codes(client)
    assert found["mode_unwatched"]["params"]["modes"] == "night"


async def test_ready_when_nothing_is_missing(hass, hass_ws_client):
    entry = make_entry(extra_subentries=[
        sub("notification", "Phone", {"service": "notify", "categories": ["alarm"]}, "n1"),
        sub("siren", "Siren", {"control": "siren.x", "causes": ["intrusion"]}, "s1"),
    ])
    for it in entry.options["items"].values():
        if it["type"] == "zone":
            it["data"]["battery_entity"] = "sensor.b"
    entry, client = await _client(hass, hass_ws_client, entry)
    assert await _codes(client) == {}


async def test_tamper_on_the_same_device_that_is_not_connected_is_found(hass, hass_ws_client):
    entry, client = await _client(hass, hass_ws_client)
    other = MockConfigEntry(domain="test")
    other.add_to_hass(hass)
    dev = _device(hass, other, "d", "Door")
    _add(hass, other, "binary_sensor", "front_dev", dev, "door")
    _add(hass, other, "binary_sensor", "front_dev_tamper", dev, "tamper")
    for it in entry.options["items"].values():
        if it["title"] == "Front door":
            it["data"]["entity_id"] = "binary_sensor.front_dev"
    found = await _codes(client)
    assert found["tamper_unlinked"]["params"] == {"n": "1", "names": "Front door"}


async def test_default_groups_are_added_once_and_only_when_missing(hass, hass_ws_client):
    entry = _empty()
    entry, client = await _client(hass, hass_ws_client, entry)
    res = await _ws(client, type="vigil_alarm/create_default_groups")
    assert res["result"]["ok"] and len(res["result"]["ids"]) == 2
    await hass.async_block_till_done()
    groups = {i.title: i.data for i in items_of(hass.config_entries.async_entries(DOMAIN)[0]).values()}
    assert groups["Perimeter"] == {"modes": ["home", "away", "night"], "suggest_for": "contacts"}
    assert groups["Interior"] == {"modes": ["away"], "suggest_for": "motion"}
    again = await _ws(client, type="vigil_alarm/create_default_groups")
    assert again["result"]["ids"] == []


async def test_default_groups_keep_a_kind_the_person_already_has(hass, hass_ws_client):
    keep = sub("sensor_group", "Mine", {"modes": ["away"], "suggest_for": "contacts"}, "mine")
    entry = make_entry(extra_subentries=[keep])
    for sid in [k for k, v in entry.options["items"].items() if v["type"] in ("zone", "sensor_group") and k != "mine"]:
        entry.options["items"].pop(sid)
    entry, client = await _client(hass, hass_ws_client, entry)
    res = await _ws(client, type="vigil_alarm/create_default_groups")
    assert len(res["result"]["ids"]) == 1  # only the motion group


async def test_a_phone_is_offered_as_the_first_channel_and_added_with_the_usual_categories(hass, hass_ws_client):
    async def _noop(call):
        pass

    hass.services.async_register("notify", "mobile_app_annas_phone", _noop)
    hass.services.async_register("notify", "mobile_app_bobs_phone", _noop)
    hass.services.async_register("notify", "persistent_notification", _noop)
    entry, client = await _client(hass, hass_ws_client)
    found = (await _codes(client))["no_notification"]
    assert found["go"] == "add_phone"
    assert [p["service"] for p in found["phones"]] == ["mobile_app_annas_phone", "mobile_app_bobs_phone"]
    assert found["phones"][0]["title"] == "Annas Phone"
    res = await _ws(client, type="vigil_alarm/add_phone", service="mobile_app_annas_phone")
    assert res["result"] == {"ok": True, "id": res["result"]["id"], "title": "Annas Phone"}
    await hass.async_block_till_done()
    chan = next(i for i in items_of(hass.config_entries.async_entries(DOMAIN)[0]).values() if i.title == "Annas Phone")
    assert chan.data["service"] == "mobile_app_annas_phone"
    assert set(chan.data["categories"]) == {"alarm", "pending", "fault", "technical"}
    # the channel exists now: no more problem, and that phone is not offered again
    again = await _ws(client, type="vigil_alarm/readiness")
    assert "no_notification" not in {f["code"] for f in again["result"]["findings"]}
    refused = await _ws(client, type="vigil_alarm/add_phone", service="mobile_app_annas_phone")
    assert refused["result"]["ok"] is False


async def test_without_a_phone_the_channel_problem_points_to_the_notifications_tab(hass, hass_ws_client):
    entry, client = await _client(hass, hass_ws_client)
    found = (await _codes(client))["no_notification"]
    assert found["go"] == "notification" and found["phones"] == []


async def test_dashboard_has_this_installations_own_entity_ids(hass, hass_ws_client):
    import yaml

    entry, client = await _client(hass, hass_ws_client)
    res = await _ws(client, type="vigil_alarm/dashboard")
    board = yaml.safe_load(res["result"]["yaml"])
    cards = board["views"][0]["cards"]
    text = res["result"]["yaml"]
    assert cards[0]["entity"] == "alarm_control_panel.vigil_alarm"
    for entity in ("binary_sensor.vigil_alarm_intrusion_alarm", "binary_sensor.vigil_alarm_water_alarm",
                   "sensor.front_door_status", "switch.front_door_bypass", "event.vigil_alarm_alarm_events"):
        assert entity in text, entity
    registry = hass.data["entity_registry"]
    for card in cards:  # every entity the dashboard names exists
        for row in card.get("entities", []):
            if "entity" in row:
                assert registry.async_get(row["entity"]) is not None, row


async def test_diagnostics_hold_no_codes_tags_or_user_names(hass):
    from custom_components.vigil_alarm.diagnostics import async_get_config_entry_diagnostics

    entry = await _setup(hass, make_entry())
    out = await async_get_config_entry_diagnostics(hass, entry)
    text = str(out)
    for secret in ("Anna", "Bob", "1234", "5678"):
        assert secret not in text, secret
    users = [i for i in out["items"] if i["type"] == "user"]
    assert users and all(u["data"]["code_hash"] == "**redacted**" for u in users)
    assert any(i["title"] == "Front door" for i in out["items"])
    assert out["state"]["state"] == "disarmed"
