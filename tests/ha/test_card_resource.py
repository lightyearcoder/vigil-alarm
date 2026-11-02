"""0.7.4: the card is a dashboard resource (loaded before the dashboard is drawn), made once and moved on an update."""

from __future__ import annotations

from homeassistant.components.lovelace.const import LOVELACE_DATA
from homeassistant.setup import async_setup_component

from custom_components.vigil_alarm.panel import CARD_URL

from .test_integration import _setup


def _ours(hass):
    return [i for i in hass.data[LOVELACE_DATA].resources.async_items() if i["url"].split("?")[0] == CARD_URL]


async def test_the_card_is_made_a_dashboard_resource_once(hass):
    assert await async_setup_component(hass, "lovelace", {})
    entry = await _setup(hass)
    found = _ours(hass)
    assert len(found) == 1 and found[0]["type"] == "module" and "?v=" in found[0]["url"]
    await hass.config_entries.async_reload(entry.entry_id)  # a reload does not make a second one
    await hass.async_block_till_done()
    assert len(_ours(hass)) == 1


async def test_an_old_or_double_resource_is_moved_and_tidied(hass):
    assert await async_setup_component(hass, "lovelace", {})
    resources = hass.data[LOVELACE_DATA].resources
    await resources.async_load()
    resources.loaded = True
    await resources.async_create_item({"res_type": "module", "url": f"{CARD_URL}?v=0.1.0"})
    await resources.async_create_item({"res_type": "module", "url": f"{CARD_URL}?v=0.2.0"})
    await _setup(hass)
    found = _ours(hass)
    assert len(found) == 1 and "0.1.0" not in found[0]["url"] and "0.2.0" not in found[0]["url"]


async def test_the_resource_goes_with_the_integration(hass):
    assert await async_setup_component(hass, "lovelace", {})
    entry = await _setup(hass)
    await hass.config_entries.async_remove(entry.entry_id)
    await hass.async_block_till_done()
    assert _ours(hass) == []
