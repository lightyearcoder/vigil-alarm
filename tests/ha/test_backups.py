"""Back-ups of the configuration, the summary of a change, export and import."""

from __future__ import annotations

import copy

from custom_components.vigil_alarm.backups import KEEP, diff
from custom_components.vigil_alarm.items import items_of

from .common import make_entry
from .test_integration import _setup
from .test_panel import _client, _ws


async def _save_sensor(client, name, entity):
    return await _ws(client, type="vigil_alarm/save", kind="sensor",
                     data={"name": name, "entity_id": entity, "cls": "intrusion", "type": "instant",
                           "sensor_groups": ["g_all"], "at_arm_open": "wait_clear"})


async def _versions(client):
    res = await _ws(client, type="vigil_alarm/backups")
    assert res["success"]
    return res["result"]["versions"]


async def test_every_change_keeps_the_state_before(hass, hass_ws_client):
    entry, client = await _client(hass, hass_ws_client)
    assert await _versions(client) == []
    res = await _save_sensor(client, "Garage", "binary_sensor.garage")
    assert res["result"]["ok"]
    await hass.async_block_till_done()
    versions = await _versions(client)
    assert len(versions) == 1
    v = versions[0]
    assert v["reason"] == "edit"
    assert v["summary"]["counts"] == {"zone": {"added": 1}}
    assert v["summary"]["items"] == [{"type": "zone", "action": "added", "name": "Garage"}]


async def test_restore_brings_back_the_old_state_and_can_be_undone(hass, hass_ws_client):
    entry, client = await _client(hass, hass_ws_client)
    before = copy.deepcopy(dict(entry.options["items"]))
    await _save_sensor(client, "Garage", "binary_sensor.garage")
    await hass.async_block_till_done()
    assert len(items_of(entry)) == len(before) + 1
    version_id = (await _versions(client))[0]["id"]
    # preview changes nothing
    res = await _ws(client, type="vigil_alarm/backup_restore", version_id=version_id, preview=True)
    assert res["result"]["change"]["counts"] == {"zone": {"removed": 1}}
    assert len(items_of(entry)) == len(before) + 1
    res = await _ws(client, type="vigil_alarm/backup_restore", version_id=version_id)
    assert res["result"]["ok"]
    await hass.async_block_till_done()
    assert {k: v["title"] for k, v in entry.options["items"].items()} == {k: v["title"] for k, v in before.items()}
    versions = await _versions(client)
    assert [v["reason"] for v in versions] == ["restore", "edit"]
    # the restore kept the state with the garage: restoring that undoes the restore
    await _ws(client, type="vigil_alarm/backup_restore", version_id=versions[0]["id"])
    await hass.async_block_till_done()
    assert any(s.title == "Garage" for s in items_of(entry).values())


async def test_only_the_last_versions_are_kept(hass, hass_ws_client):
    entry, client = await _client(hass, hass_ws_client)
    for n in range(KEEP + 3):
        await _save_sensor(client, f"S{n}", f"binary_sensor.s{n}")
        await hass.async_block_till_done()
    versions = await _versions(client)
    assert len(versions) == KEEP
    assert versions[0]["summary"]["items"][0]["name"] == f"S{KEEP + 2}"


async def test_a_change_that_changes_nothing_is_not_kept(hass, hass_ws_client):
    entry, client = await _client(hass, hass_ws_client)
    sensor = next(z for z in (await _ws(client, type="vigil_alarm/get"))["result"]["items"]["sensor"] if z["title"] == "Smoke")
    await _ws(client, type="vigil_alarm/save", kind="sensor", subentry_id=sensor["id"],
              data={"name": "Smoke", "entity_id": "binary_sensor.smoke", "cls": "fire"})
    await hass.async_block_till_done()
    assert await _versions(client) == []


async def test_the_versions_survive_a_restart_and_a_change_made_while_stopped_is_kept(hass, hass_ws_client):
    entry, client = await _client(hass, hass_ws_client)
    await _save_sensor(client, "Garage", "binary_sensor.garage")
    await hass.async_block_till_done()
    assert await hass.config_entries.async_unload(entry.entry_id)
    items = copy.deepcopy(dict(entry.options["items"]))
    items.pop(next(k for k, v in items.items() if v["title"] == "Garage"))
    hass.config_entries.async_update_entry(entry, options={"items": items})  # changed while Vigil was off
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    client = await hass_ws_client(hass)
    versions = await _versions(client)
    assert [v["reason"] for v in versions] == ["external", "edit"]
    assert versions[0]["summary"]["counts"] == {"zone": {"removed": 1}}


async def test_export_and_import_round_trip(hass, hass_ws_client):
    entry, client = await _client(hass, hass_ws_client)
    res = await _ws(client, type="vigil_alarm/export")
    payload = res["result"]
    assert payload["format"] == "vigil_alarm_configuration" and payload["entry_version"] == 3
    assert "1234" not in str(payload)  # code hashes, never codes
    await _save_sensor(client, "Garage", "binary_sensor.garage")
    await hass.async_block_till_done()
    res = await _ws(client, type="vigil_alarm/import", payload=payload, preview=True)
    assert res["result"]["change"]["counts"] == {"zone": {"removed": 1}}
    assert any(s.title == "Garage" for s in items_of(entry).values())
    res = await _ws(client, type="vigil_alarm/import", payload=payload)
    assert res["result"]["ok"]
    await hass.async_block_till_done()
    assert not any(s.title == "Garage" for s in items_of(entry).values())
    assert (await _versions(client))[0]["reason"] == "import"  # and the garage state is kept


async def test_import_refuses_files_it_cannot_use(hass, hass_ws_client):
    entry, client = await _client(hass, hass_ws_client)
    good = (await _ws(client, type="vigil_alarm/export"))["result"]

    async def refused(payload):
        res = await _ws(client, type="vigil_alarm/import", payload=payload)
        assert res["result"]["ok"] is False
        return res["result"]["errors"]["base"]

    assert await refused({"hello": 1}) == "import_not_vigil"
    assert await refused({**good, "format_version": 99}) == "import_format_version"
    assert await refused({**good, "entry_version": 2}) == "import_entry_version"
    broken = copy.deepcopy(good)
    broken["options"]["items"]["front"]["type"] = "nonsense"
    assert await refused(broken) == "backup_invalid"
    broken = copy.deepcopy(good)
    broken["data"]["modes"] = []
    assert await refused(broken) in ("invalid_config", "backup_invalid")
    broken = copy.deepcopy(good)
    broken["data"] = "text"
    assert await refused(broken) == "backup_invalid"
    assert await _versions(client) == []  # nothing was applied


async def test_save_many_can_preview(hass, hass_ws_client):
    entry, client = await _client(hass, hass_ws_client)
    items = [{"name": "A", "entity_id": "binary_sensor.a", "cls": "intrusion", "type": "instant", "sensor_groups": ["g_all"], "at_arm_open": "wait_clear"},
             {"name": "B", "entity_id": "binary_sensor.b", "cls": "intrusion", "type": "instant", "sensor_groups": ["g_all"], "at_arm_open": "wait_clear"}]
    n = len(items_of(entry))
    res = await _ws(client, type="vigil_alarm/save_many", items=items, preview=True)
    assert res["result"]["change"]["counts"] == {"zone": {"added": 2}}
    assert len(items_of(entry)) == n
    res = await _ws(client, type="vigil_alarm/save_many", items=items)
    assert res["result"]["change"]["counts"] == {"zone": {"added": 2}}
    await hass.async_block_till_done()
    assert len(items_of(entry)) == n + 2


async def test_backup_commands_are_admin_only(hass, hass_ws_client, hass_read_only_access_token):
    await _setup(hass, make_entry())
    client = await hass_ws_client(hass, hass_read_only_access_token)
    for msg in ({"type": "vigil_alarm/backups"}, {"type": "vigil_alarm/backup_restore", "version_id": "x"},
                {"type": "vigil_alarm/export"}, {"type": "vigil_alarm/import", "payload": {}}):
        res = await _ws(client, **msg)
        assert res["success"] is False and res["error"]["code"] == "unauthorized"


def test_diff_names_and_keys_but_never_values():
    old = {"data": {"modes": ["home"], "heartbeat_url": "https://secret/1"}, "options": {"items": {
        "a": {"type": "zone", "title": "A", "data": {}}}}}
    new = {"data": {"modes": ["home"], "heartbeat_url": "https://secret/2"}, "options": {"items": {
        "a": {"type": "zone", "title": "A2", "data": {}},
        "t": {"type": "zone", "title": "T", "data": {"companion_of": "a"}}}}}
    d = diff(old, new)
    assert d["settings"] == ["heartbeat_url"]
    assert d["items"] == [{"type": "zone", "action": "changed", "name": "A2"}]  # companion left out
    assert "secret" not in str(d)


async def test_the_number_of_versions_is_a_setting(hass, hass_ws_client):
    entry, client = await _client(hass, hass_ws_client)
    snap = (await _ws(client, type="vigil_alarm/get"))["result"]
    assert snap["entry"]["data"]["backup_versions"] == 10  # the default
    assert any(f["key"] == "backup_versions" for f in snap["settings_form"])
    data = {**snap["entry"]["data"]}
    for bad in (0, 51, "x"):
        res = await _ws(client, type="vigil_alarm/save_settings", data={**data, "backup_versions": bad})
        assert res["result"]["errors"] == {"backup_versions": "backup_versions_range"}
    res = await _ws(client, type="vigil_alarm/save_settings", data={**data, "backup_versions": 3})
    assert res["result"]["ok"]
    await hass.async_block_till_done()
    client = await hass_ws_client(hass)
    for n in range(6):
        await _save_sensor(client, f"S{n}", f"binary_sensor.s{n}")
        await hass.async_block_till_done()
    assert len(await _versions(client)) == 3  # the settings change itself was a version too, and has dropped off


async def test_lowering_the_setting_drops_the_oldest_versions_at_once(hass, hass_ws_client):
    entry, client = await _client(hass, hass_ws_client)
    for n in range(5):
        await _save_sensor(client, f"S{n}", f"binary_sensor.s{n}")
        await hass.async_block_till_done()
    assert len(await _versions(client)) == 5
    data = {**(await _ws(client, type="vigil_alarm/get"))["result"]["entry"]["data"], "backup_versions": 2}
    await _ws(client, type="vigil_alarm/save_settings", data=data)
    await hass.async_block_till_done()
    client = await hass_ws_client(hass)
    assert len(await _versions(client)) == 2


async def test_an_update_keeps_the_configuration_from_before_with_the_version_that_made_it(hass, hass_ws_client, hass_storage):
    entry, client = await _client(hass, hass_ws_client)
    key = f"vigil_alarm.backups.{entry.entry_id}"
    assert await hass.config_entries.async_unload(entry.entry_id)
    # Vigil 0.4.0 wrote this configuration in storage format 2; the update migrated it (here: one sensor less)
    meta = hass_storage[key]["data"]["meta"]
    hass_storage[key]["data"]["meta"] = {**meta, "entry_version": 2, "integration_version": "0.4.0"}
    items = copy.deepcopy(dict(entry.options["items"]))
    items.pop(next(k for k, v in items.items() if v["title"] == "Smoke"))
    hass.config_entries.async_update_entry(entry, options={"items": items})
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    client = await hass_ws_client(hass)
    res = await _ws(client, type="vigil_alarm/backups")
    old = res["result"]["versions"][0]
    assert old["reason"] == "upgrade" and old["integration_version"] == "0.4.0" and old["entry_version"] == 2
    assert old["restorable"] is False and res["result"]["entry_version"] == 3
    # the old format cannot be put back (it would need a migration): refused, nothing changes
    res = await _ws(client, type="vigil_alarm/backup_restore", version_id=old["id"])
    assert res["result"]["ok"] is False and res["result"]["errors"] == {"base": "import_entry_version"}
    # a change from now on is a version of the new format
    await _save_sensor(client, "Garage", "binary_sensor.garage")
    await hass.async_block_till_done()
    new = (await _versions(client))[0]
    assert new["restorable"] is True and new["integration_version"] == "0.5.0" and new["entry_version"] == 3
