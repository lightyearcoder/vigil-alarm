from __future__ import annotations

import logging
from datetime import timedelta

import aiohttp
from homeassistant.helpers import issue_registry as ir
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import async_fire_time_changed

from custom_components.vigil_alarm.const import DOMAIN
from custom_components.vigil_alarm.diagnostics import async_get_config_entry_diagnostics
from custom_components.vigil_alarm.heartbeat import FIRST_PING_DELAY, valid_url

from .test_integration import _setup
from .test_panel import _client, _ws
from .test_sirens import _house

URL = "https://hc-ping.example.org/0123abcd-secret-key"


def issues(hass):
    return {i.translation_key for i in ir.async_get(hass).issues.values() if i.domain == DOMAIN}


def test_only_web_addresses_are_accepted():
    assert valid_url(URL) and valid_url("http://192.168.1.5:8080/ping")
    for bad in ("", None, "ftp://x.y/z", "hc-ping.example.org/x", "https://", "javascript:alert(1)", "https://x.y/" + "a" * 3000):
        assert not valid_url(bad)


async def test_no_address_means_no_calls(hass, aioclient_mock):
    entry = await _house(hass)
    assert entry.runtime_data.heartbeat.enabled is False
    assert await entry.runtime_data.heartbeat.ping() is False
    assert aioclient_mock.call_count == 0


async def test_it_pings_soon_after_start_and_then_on_the_interval_also_when_disarmed(hass, aioclient_mock, freezer):
    aioclient_mock.get(URL, text="OK")
    entry = await _house(hass, heartbeat_url=URL, heartbeat_interval_minutes=5)
    freezer.tick(timedelta(seconds=FIRST_PING_DELAY + 1))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert aioclient_mock.call_count == 1
    freezer.tick(timedelta(minutes=5))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert aioclient_mock.call_count == 2
    status = entry.runtime_data.heartbeat.status()
    assert status["last_ok"] and status["failures"] == 0 and status["reason"] is None


async def test_the_call_carries_nothing_about_the_alarm(hass, aioclient_mock):
    aioclient_mock.get(URL, text="OK")
    entry = await _house(hass, heartbeat_url=URL)
    await entry.runtime_data.heartbeat.ping()
    (method, url, data, headers) = aioclient_mock.mock_calls[0]
    assert str(url) == URL and not data
    assert not any(k.lower() in ("x-alarm", "authorization") for k in (headers or {}))


async def test_failures_are_named_without_the_address_and_a_repair_follows_after_three(hass, aioclient_mock, caplog):
    caplog.set_level(logging.DEBUG)
    aioclient_mock.get(URL, status=404)
    entry = await _house(hass, heartbeat_url=URL)
    beat = entry.runtime_data.heartbeat
    for _ in range(2):
        assert await beat.ping() is False
    assert beat.status()["reason"] == "http_404" and issues(hass) == set()
    await beat.ping()
    await hass.async_block_till_done()
    assert issues(hass) == {"heartbeat_failing"}
    aioclient_mock.clear_requests()
    aioclient_mock.get(URL, exc=aiohttp.ClientConnectionError(URL))
    await beat.ping()
    assert beat.status()["reason"] == "connection"
    aioclient_mock.clear_requests()
    aioclient_mock.get(URL, text="OK")
    assert await beat.ping() is True
    await hass.async_block_till_done()
    assert issues(hass) == set() and beat.status()["failures"] == 0
    # (the test harness itself writes every storage write to the debug log; Home Assistant does not)
    logged = "\n".join(r.getMessage() for r in caplog.records if not r.name.startswith("pytest_homeassistant"))
    assert "secret-key" not in logged and "hc-ping" not in logged


async def test_the_address_is_a_secret(hass, hass_ws_client, aioclient_mock):
    aioclient_mock.get(URL, text="OK")
    entry, client = await _client(hass, hass_ws_client)
    snap = (await _ws(client, type="vigil_alarm/get"))["result"]["entry"]["data"]
    ok = await _ws(client, type="vigil_alarm/save_settings", data={**snap, "heartbeat_url": f"  {URL}  ", "heartbeat_interval_minutes": 10})
    assert ok["result"]["ok"] is True
    await hass.async_block_till_done()
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    assert entry.data["heartbeat_url"] == URL
    out = await async_get_config_entry_diagnostics(hass, entry)
    assert "secret-key" not in str(out) and out["settings"]["heartbeat_url"] == "**redacted**"
    status = (await _ws(client, type="vigil_alarm/heartbeat", test=True))["result"]
    assert status["enabled"] and status["last_ok"] and "secret-key" not in str(status)
    assert aioclient_mock.call_count >= 1


async def test_settings_are_checked(hass, hass_ws_client):
    entry, client = await _client(hass, hass_ws_client)
    snap = (await _ws(client, type="vigil_alarm/get"))["result"]["entry"]["data"]
    assert snap["heartbeat_interval_minutes"] == 5 and not snap.get("heartbeat_url")
    bad = await _ws(client, type="vigil_alarm/save_settings", data={**snap, "heartbeat_url": "not a url"})
    assert bad["result"]["errors"] == {"heartbeat_url": "heartbeat_url_invalid"}
    bad = await _ws(client, type="vigil_alarm/save_settings", data={**snap, "heartbeat_interval_minutes": 0})
    assert bad["result"]["errors"] == {"heartbeat_interval_minutes": "heartbeat_range"}
    off = await _ws(client, type="vigil_alarm/save_settings", data={**snap, "heartbeat_url": ""})
    assert off["result"]["ok"] is True
    status = (await _ws(client, type="vigil_alarm/heartbeat"))["result"]
    assert status["enabled"] is False
