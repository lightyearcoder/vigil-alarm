from __future__ import annotations

from homeassistant.helpers import device_registry as dr, entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.vigil_alarm.const import DOMAIN
from custom_components.vigil_alarm.items import items_of

from .common import make_entry
from .test_integration import _setup
from .test_panel import _client, _ws


def _add(hass, config, domain, uid, device=None, cls=None, **kw):
    reg = er.async_get(hass)
    return reg.async_get_or_create(
        domain, "test", uid, config_entry=config, device_id=device.id if device else None,
        original_device_class=cls, suggested_object_id=uid, **kw,
    )


def _device(hass, config, ident, name):
    return dr.async_get(hass).async_get_or_create(
        config_entry_id=config.entry_id, identifiers={("test", ident)}, name=name
    )


async def test_discovery_groups_battery_and_tamper_per_device(hass, hass_ws_client):
    entry, client = await _client(hass, hass_ws_client)
    other = MockConfigEntry(domain="test")
    other.add_to_hass(hass)
    door = _device(hass, other, "d1", "Back door")
    pir = _device(hass, other, "d2", "Hall PIR")
    _add(hass, other, "binary_sensor", "back_door", door, "door")
    _add(hass, other, "sensor", "back_door_battery", door, "battery", unit_of_measurement="%")
    _add(hass, other, "binary_sensor", "back_door_tamper", door, "tamper")
    _add(hass, other, "binary_sensor", "hall_pir", pir, "motion")
    _add(hass, other, "binary_sensor", "kitchen_leak", None, "moisture")
    _add(hass, other, "binary_sensor", "lonely_tamper", None, "tamper")
    _add(hass, other, "binary_sensor", "ignored", None, "light")
    _add(hass, other, "binary_sensor", "boiler_heat", None, "heat")
    _add(hass, other, "binary_sensor", "radar", None, "moving")
    _add(hass, other, "binary_sensor", "panic_button", None, "safety")
    _add(hass, other, "binary_sensor", "door_lock", None, "lock")
    _add(hass, other, "binary_sensor", "shock", None, "vibration")
    res = await _ws(client, type="vigil_alarm/discover")
    assert res["success"]
    by_id = {c["entity_id"]: c for c in res["result"]["candidates"]}
    back = by_id["binary_sensor.back_door"]
    assert back["name"] == "Back door"
    assert (back["cls"], back["zone"], back["entrance"]) == ("intrusion", "perimeter", True)
    assert back["battery_entity"] == "sensor.back_door_battery"
    assert back["tamper_entity"] == "binary_sensor.back_door_tamper"
    pir_c = by_id["binary_sensor.hall_pir"]
    assert (pir_c["zone"], pir_c["entrance"], pir_c["battery_entity"]) == ("interior", False, None)
    assert by_id["binary_sensor.kitchen_leak"]["cls"] == "water"
    assert "binary_sensor.ignored" not in by_id
    assert (by_id["binary_sensor.boiler_heat"]["cls"], by_id["binary_sensor.boiler_heat"]["zone"]) == ("fire", None)
    assert (by_id["binary_sensor.radar"]["cls"], by_id["binary_sensor.radar"]["zone"]) == ("intrusion", "interior")
    assert by_id["binary_sensor.panic_button"]["cls"] == "alarm24"
    assert "binary_sensor.door_lock" not in by_id and "binary_sensor.shock" not in by_id  # not offered on purpose
    # a tamper contact that belongs to a listed sensor is not offered twice
    assert [t["entity_id"] for t in res["result"]["tamper_only"]] == ["binary_sensor.lonely_tamper"]


async def test_discovery_marks_sensors_already_in_use_and_skips_disabled(hass, hass_ws_client):
    entry, client = await _client(hass, hass_ws_client)
    other = MockConfigEntry(domain="test")
    other.add_to_hass(hass)
    mine = _add(hass, other, "binary_sensor", "porch_door", None, "door")
    for item in entry.options["items"].values():  # use it in the alarm as if the person had added it
        if item["title"] == "Front door":
            item["data"]["entity_id"] = mine.entity_id
    _add(hass, other, "binary_sensor", "off", None, "window", disabled_by=er.RegistryEntryDisabler.USER)
    res = await _ws(client, type="vigil_alarm/discover")
    by_id = {c["entity_id"]: c for c in res["result"]["candidates"]}
    assert by_id[mine.entity_id]["in_use"] is True
    assert "binary_sensor.off" not in by_id


async def test_discovery_report_is_anonymous(hass, hass_ws_client):
    entry, client = await _client(hass, hass_ws_client)
    other = MockConfigEntry(domain="test")
    other.add_to_hass(hass)
    door = _device(hass, other, "secret-ident-1", "Dave's bedroom door")
    _add(hass, other, "binary_sensor", "daves_door", door, "door")
    _add(hass, other, "binary_sensor", "daves_door_tamper", door, "tamper")
    res = await _ws(client, type="vigil_alarm/discover_report")
    rows = res["result"]["entities"]
    assert {r["device_class"] for r in rows} == {"door", "tamper"}
    assert {r["device"] for r in rows} == {1}  # same device, numbered
    text = str(res["result"]).lower()
    for leak in ("dave", "secret", "bedroom", "binary_sensor."):
        assert leak not in text


async def test_discovery_needs_admin(hass, hass_ws_client, hass_admin_user):
    entry, client = await _client(hass, hass_ws_client)
    hass_admin_user.groups = []
    res = await _ws(client, type="vigil_alarm/discover")
    assert not res["success"]


def _sensor(name, entity, **extra):
    return {"name": name, "entity_id": entity, "cls": "intrusion", "type": "instant",
            "sensor_groups": ["g_all"], "at_arm_open": "bypass", **extra}


async def test_save_many_adds_all_with_their_tamper_companions_in_one_go(hass, hass_ws_client):
    entry, client = await _client(hass, hass_ws_client)
    before = len(items_of(entry))
    res = await _ws(client, type="vigil_alarm/save_many", items=[
        _sensor("Back door", "binary_sensor.back_door", tamper_entity="binary_sensor.back_door_tamper"),
        _sensor("Hall PIR", "binary_sensor.hall_pir"),
    ])
    assert res["success"] and res["result"]["ok"] and len(res["result"]["ids"]) == 2
    await hass.async_block_till_done()
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    titles = {i.title for i in items_of(entry).values()}
    assert {"Back door", "Hall PIR", "Back door (tamper)"} <= titles
    assert len(items_of(entry)) == before + 3


async def test_save_many_saves_nothing_when_one_fails(hass, hass_ws_client):
    entry, client = await _client(hass, hass_ws_client)
    before = dict(entry.options["items"])
    res = await _ws(client, type="vigil_alarm/save_many", items=[
        _sensor("Back door", "binary_sensor.back_door"),
        _sensor("Hall PIR", "binary_sensor.back_door"),  # same entity as the one before
    ])
    result = res["result"]
    assert result["ok"] is False and result["index"] == 1
    assert result["errors"] == {"entity_id": "entity_in_use"}
    await hass.async_block_till_done()
    assert hass.config_entries.async_entries(DOMAIN)[0].options["items"] == before


async def test_save_many_refuses_a_name_used_earlier_in_the_same_batch(hass, hass_ws_client):
    entry, client = await _client(hass, hass_ws_client)
    res = await _ws(client, type="vigil_alarm/save_many", items=[
        _sensor("Door", "binary_sensor.a"), _sensor("Door", "binary_sensor.b"),
    ])
    assert res["result"]["index"] == 1 and res["result"]["errors"] == {"name": "name_in_use"}


async def test_discovery_proposes_the_groups_marked_for_new_sensors(hass, hass_ws_client):
    from .common import sub

    group = sub("sensor_group", "Shell", {"modes": ["home", "away"], "suggest_for": "contacts"}, "g_shell")
    entry, client = await _client(hass, hass_ws_client, extra_subentries=[group])
    other = MockConfigEntry(domain="test")
    other.add_to_hass(hass)
    _add(hass, other, "binary_sensor", "side_door", None, "door")
    _add(hass, other, "binary_sensor", "attic_pir", None, "motion")
    res = await _ws(client, type="vigil_alarm/discover")
    by_id = {c["entity_id"]: c for c in res["result"]["candidates"]}
    assert by_id["binary_sensor.side_door"]["groups"] == ["g_shell"]
    assert by_id["binary_sensor.attic_pir"]["groups"] == []


async def test_discovery_says_which_integration_an_entity_comes_from(hass, hass_ws_client):
    entry, client = await _client(hass, hass_ws_client)
    other = MockConfigEntry(domain="test")
    other.add_to_hass(hass)
    _add(hass, other, "binary_sensor", "somewhere_door", None, "door")
    res = await _ws(client, type="vigil_alarm/discover")
    by_id = {c["entity_id"]: c for c in res["result"]["candidates"]}
    assert by_id["binary_sensor.somewhere_door"]["platform"] == "test"


async def test_discovery_uses_a_battery_low_flag_only_when_there_is_no_percentage(hass, hass_ws_client):
    entry, client = await _client(hass, hass_ws_client)
    other = MockConfigEntry(domain="test")
    other.add_to_hass(hass)
    flag_only = _device(hass, other, "a", "Flag only")
    both = _device(hass, other, "b", "Both")
    _add(hass, other, "binary_sensor", "flag_door", flag_only, "door")
    _add(hass, other, "binary_sensor", "flag_door_low", flag_only, "battery")
    _add(hass, other, "binary_sensor", "both_door", both, "door")
    _add(hass, other, "binary_sensor", "both_door_low", both, "battery")
    _add(hass, other, "sensor", "both_door_pct", both, "battery", unit_of_measurement="%")
    res = await _ws(client, type="vigil_alarm/discover")
    by_id = {c["entity_id"]: c for c in res["result"]["candidates"]}
    assert by_id["binary_sensor.flag_door"]["battery_entity"] == "binary_sensor.flag_door_low"
    assert by_id["binary_sensor.both_door"]["battery_entity"] == "sensor.both_door_pct"
