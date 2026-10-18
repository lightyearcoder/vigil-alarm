from __future__ import annotations

import csv
import io
import json

from custom_components.vigil_alarm.const import DOMAIN

from .test_integration import _call, _setup
from .test_panel import _client, _ws


async def _log(client, **kw):
    res = await _ws(client, type="vigil_alarm/log", **kw)
    assert res["success"]
    return res["result"]


async def test_every_event_lands_in_the_log_newest_first_without_codes(hass, hass_ws_client):
    entry, client = await _client(hass, hass_ws_client)
    await _call(hass, "alarm_arm_home", code="1234")
    await hass.async_block_till_done()
    await _call(hass, "alarm_disarm", code="1234")
    await hass.async_block_till_done()
    result = await _log(client)
    kinds = [e["event"] for e in result["entries"]]
    assert kinds[:2] == ["disarmed", "armed"]
    armed = result["entries"][1]
    assert armed["user"] == "Anna" and armed["result"] == "home"
    assert armed["time"].endswith("Z") and len(armed["time"]) == 20  # RFC 3339, UTC
    assert "1234" not in json.dumps(result)
    assert result["labels"]["armed"] and result["retention_days"] == 90


async def test_the_log_keeps_the_user_and_the_panel_apart(hass, hass_ws_client):
    entry, client = await _client(hass, hass_ws_client)
    await entry.runtime_data.async_arm("home", "1234", "vigil-panel-garage")
    await hass.async_block_till_done()
    await entry.runtime_data.async_disarm("1234", "vigil-panel-garage")
    await hass.async_block_till_done()
    result = await _log(client)
    for e in (x for x in result["entries"] if x["event"] in ("armed", "disarmed")):
        assert e["user"] == "Anna" and e["source"] == "vigil-panel-garage"


async def test_an_unbypass_by_the_disarm_names_the_user_and_the_panel(hass, hass_ws_client):
    entry, client = await _client(hass, hass_ws_client)
    manager = entry.runtime_data
    await manager.async_arm("home", "1234", "vigil-panel-garage")
    await hass.async_block_till_done()
    sid = next(iter(manager.config.sensors))
    manager.engine.bypass(sid)
    await manager.async_disarm("1234", "vigil-panel-garage")
    await hass.async_block_till_done()
    result = await _log(client)
    lifted = next(e for e in result["entries"] if e["event"] == "sensor_unbypassed")
    assert lifted["user"] == "Anna" and lifted["source"] == "vigil-panel-garage"


async def test_the_log_names_the_sensor_that_started_the_entry_delay(hass, hass_ws_client):
    entry, client = await _client(hass, hass_ws_client)
    await _call(hass, "alarm_arm_home", code="1234")
    await hass.async_block_till_done()
    hass.states.async_set("binary_sensor.front_door", "on")
    await hass.async_block_till_done()
    result = await _log(client, limit=50)
    pending = next(e for e in result["entries"] if e["event"] == "pending_started")
    assert pending["item"] == "Front door"
    assert "end" in pending["detail"]


async def test_export_as_json_lines_and_csv_hold_the_same_entries(hass, hass_ws_client):
    entry, client = await _client(hass, hass_ws_client)
    await _call(hass, "alarm_arm_home", code="1234")
    await hass.async_block_till_done()
    jl = (await _ws(client, type="vigil_alarm/log_export", format="jsonl"))["result"]
    assert jl["filename"].endswith(".jsonl") and jl["text"].endswith("\n")
    rows = [json.loads(line) for line in jl["text"].splitlines()]
    cs = (await _ws(client, type="vigil_alarm/log_export", format="csv"))["result"]
    assert cs["filename"].endswith(".csv") and "\r\n" in cs["text"]  # RFC 4180
    table = list(csv.DictReader(io.StringIO(cs["text"])))
    assert [r["event"] for r in table] == [r["event"] for r in rows]
    assert list(table[0]) == ["time", "event", "source", "user", "item", "result", "detail"]
    assert rows == sorted(rows, key=lambda r: r["time"])  # oldest first in a file


async def test_old_entries_are_dropped_after_the_retention_time(hass, hass_ws_client):
    entry, client = await _client(hass, hass_ws_client)
    manager = entry.runtime_data
    manager.eventlog.entries.insert(0, {"time": "2000-01-01T00:00:00Z", "event": "armed", "detail": None})
    manager.eventlog.add({"t": manager._wall(), "type": "disarmed"})
    assert all(e["time"] > "2001" for e in manager.eventlog.entries)


async def test_the_log_survives_a_reload(hass, hass_ws_client):
    entry, client = await _client(hass, hass_ws_client)
    await _call(hass, "alarm_arm_home", code="1234")
    await hass.async_block_till_done()
    before = len((await _log(client))["entries"])
    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    assert len((await _log(client))["entries"]) >= before


async def test_retention_is_a_setting_with_limits(hass, hass_ws_client):
    entry, client = await _client(hass, hass_ws_client)
    snap = (await _ws(client, type="vigil_alarm/get"))["result"]
    data = {**snap["entry"]["data"], "log_retention_days": 0}
    bad = await _ws(client, type="vigil_alarm/save_settings", data=data)
    assert bad["result"]["errors"] == {"log_retention_days": "log_retention_range"}
    ok = await _ws(client, type="vigil_alarm/save_settings", data={**data, "log_retention_days": 30})
    assert ok["result"]["ok"] is True
    await hass.async_block_till_done()
    assert hass.config_entries.async_entries(DOMAIN)[0].data["log_retention_days"] == 30
