"""A sensor with its own tamper contact: one form, two sensors."""

from __future__ import annotations

from custom_components.vigil_alarm.items import items_of

from .test_panel import _client, _ws

DOOR = {
    "name": "Garage door", "entity_id": "binary_sensor.garage", "cls": "intrusion", "type": "instant",
    "sensor_groups": ["g_away"], "tamper_entity": "binary_sensor.garage_tamper",
}


def _companions(entry):
    return [s for s in items_of(entry).values() if s.data.get("companion_of")]


async def _save(client, **kw):
    return (await _ws(client, type="vigil_alarm/save", kind="sensor", **kw))["result"]


async def test_the_tamper_contact_becomes_a_sensor_of_its_own(hass, hass_ws_client):
    entry, client = await _client(hass, hass_ws_client)
    res = await _save(client, data=DOOR)
    assert res["ok"] is True
    await hass.async_block_till_done()
    [tamper] = _companions(entry)
    assert tamper.title == "Garage door (tamper)" and tamper.data["cls"] == "tamper"
    assert tamper.data["entity_id"] == "binary_sensor.garage_tamper" and tamper.data["companion_of"] == res["id"]
    assert items_of(entry)[res["id"]].data["tamper_entity"] == "binary_sensor.garage_tamper"
    # its own status and bypass switch: tamper stays separately bypassable
    assert hass.states.get("switch.garage_door_tamper_bypass") is not None
    assert hass.states.get("sensor.garage_door_tamper_status") is not None


async def test_the_tamper_contact_gives_an_alarm_even_when_disarmed(hass, hass_ws_client):
    entry, client = await _client(hass, hass_ws_client)
    await _save(client, data=DOOR)
    await hass.async_block_till_done()
    hass.states.async_set("binary_sensor.garage_tamper", "on")
    await hass.async_block_till_done()
    attrs = hass.states.get("alarm_control_panel.vigil_alarm").attributes
    assert hass.states.get("alarm_control_panel.vigil_alarm").state == "triggered"
    assert attrs["cause"] == "tamper" and attrs["cause_sensor"] == "Garage door (tamper)"


async def test_changing_the_sensor_changes_the_tamper_contact_with_it(hass, hass_ws_client):
    entry, client = await _client(hass, hass_ws_client)
    sid = (await _save(client, data=DOOR))["id"]
    await hass.async_block_till_done()
    [first] = _companions(entry)
    first_id = first.subentry_id

    await _save(client, subentry_id=sid, data={**DOOR, "name": "Side door", "tamper_entity": "binary_sensor.other"})
    await hass.async_block_till_done()
    [tamper] = _companions(entry)
    assert tamper.subentry_id == first_id  # the same one, so its bypass and history stay
    assert tamper.title == "Side door (tamper)" and tamper.data["entity_id"] == "binary_sensor.other"

    await _save(client, subentry_id=sid, data={k: v for k, v in DOOR.items() if k != "tamper_entity"})
    await hass.async_block_till_done()
    assert _companions(entry) == []


async def test_deleting_the_sensor_deletes_its_tamper_contact(hass, hass_ws_client):
    entry, client = await _client(hass, hass_ws_client)
    sid = (await _save(client, data=DOOR))["id"]
    await hass.async_block_till_done()
    res = await _ws(client, type="vigil_alarm/delete", subentry_id=sid)
    assert res["result"]["ok"] is True
    await hass.async_block_till_done()
    assert _companions(entry) == [] and sid not in items_of(entry)


async def test_the_tamper_contact_is_not_edited_or_deleted_by_itself(hass, hass_ws_client):
    entry, client = await _client(hass, hass_ws_client)
    await _save(client, data=DOOR)
    await hass.async_block_till_done()
    [tamper] = _companions(entry)
    res = await _ws(client, type="vigil_alarm/delete", subentry_id=tamper.subentry_id)
    assert res["success"] is False
    res = await _ws(client, type="vigil_alarm/save", kind="sensor", subentry_id=tamper.subentry_id, data=DOOR)
    assert res["success"] is False


async def test_mistakes_with_the_tamper_entity(hass, hass_ws_client):
    entry, client = await _client(hass, hass_ws_client)
    res = await _save(client, data={**DOOR, "tamper_entity": "binary_sensor.garage"})
    assert res["errors"] == {"tamper_entity": "tamper_same_entity"}
    res = await _save(client, data={**DOOR, "tamper_entity": "binary_sensor.front_door"})  # already a sensor
    assert res["errors"] == {"tamper_entity": "tamper_entity_in_use"}
    await _save(client, data={**DOOR, "name": "Other", "entity_id": "binary_sensor.other", "tamper_entity": None})
    # a sensor that is called like the companion would be
    await _save(client, data={**DOOR, "name": "Door two (tamper)", "entity_id": "binary_sensor.two", "tamper_entity": None})
    res = await _save(client, data={**DOOR, "name": "Door two", "entity_id": "binary_sensor.three",
                                    "tamper_entity": "binary_sensor.three_tamper"})
    assert res["errors"] == {"name": "name_in_use"}
    assert _companions(entry) == []


async def test_a_tamper_sensor_has_no_tamper_entity_of_its_own(hass, hass_ws_client):
    entry, client = await _client(hass, hass_ws_client)
    res = await _save(client, data={"name": "Box", "entity_id": "binary_sensor.box", "cls": "tamper",
                                    "tamper_entity": "binary_sensor.box_tamper"})
    assert res["ok"] is True
    await hass.async_block_till_done()
    assert "tamper_entity" not in items_of(entry)[res["id"]].data and _companions(entry) == []


async def test_one_entity_is_one_sensor(hass, hass_ws_client):
    entry, client = await _client(hass, hass_ws_client)
    base = {"name": "Twin", "entity_id": "binary_sensor.front_door", "cls": "intrusion", "type": "instant",
            "sensor_groups": ["g_away"]}
    assert (await _save(client, data=base))["errors"] == {"entity_id": "entity_in_use"}
    # the tamper contact of a sensor is a sensor too: it cannot be added a second time
    await _save(client, data=DOOR)
    await hass.async_block_till_done()
    res = await _save(client, data={**base, "name": "Tamper again", "entity_id": "binary_sensor.garage_tamper", "cls": "tamper"})
    assert res["errors"] == {"entity_id": "entity_in_use"}
    # saving a sensor again with its own entity is fine
    sid = [s.subentry_id for s in items_of(entry).values() if s.title == "Garage door"][0]
    assert (await _save(client, subentry_id=sid, data=DOOR))["ok"] is True
