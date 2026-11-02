"""The admin panel: a sidebar page to see and edit the whole configuration.

The panel only talks to this module (websocket commands, admin only). The
rules are the same as in the config flows: both use `editing`.
"""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path

from homeassistant.components import frontend, panel_custom
from homeassistant.components.http import StaticPathConfig
from homeassistant.components.lovelace.const import LOVELACE_DATA
from homeassistant.components.lovelace.resources import ResourceStorageCollection
from homeassistant.core import HomeAssistant

from .const import (
    DOMAIN,
)

PANEL_URL = "vigil_alarm"
STATIC_URL = "/vigil_alarm_static/vigil-panel.js"
PARTS_URL = "/vigil_alarm_static/panel"  # the parts of the panel script (imported by vigil-panel.js)
TEXTS_URL = "/vigil_alarm_static/texts"  # the panel texts, one file per language (imported by vigil-panel.js)
CARD_URL = "/vigil_alarm_static/vigil-card.js"  # the card for a dashboard, loaded for every user
LOGO_URL = "/vigil_alarm_static/logo.png"
_LOGGER = logging.getLogger(__name__)
_DATA_KEY = f"{DOMAIN}_panel"
_STATIC_KEY = f"{DOMAIN}_panel_static"

# Kept here, so that `from .panel import …` keeps working.
from .panel_commands import async_register_commands  # noqa: E402,F401
from .panel_forms import KINDS, TYPE_OF, form_schema, settings_schema  # noqa: E402,F401
from .panel_state import _live  # noqa: E402,F401

# ------------------------------------------------------------- panel itself


def _asset_version(version: str) -> str:
    """The version plus a short fingerprint of the two script files. While the integration is built and tested
    the version number stays the same, and a browser would keep showing the old script; with the fingerprint in
    the address every change of a file is a new address."""
    digest = hashlib.sha1()
    frontend_dir = Path(__file__).parent / "frontend"
    for path in (frontend_dir / "vigil-panel.js", frontend_dir / "vigil-card.js", *sorted((frontend_dir / "texts").glob("*.js")), *sorted((frontend_dir / "panel").glob("*.js"))):
        digest.update(path.read_bytes())
    return f"{version}-{digest.hexdigest()[:8]}"


async def _async_register_card(hass: HomeAssistant, url: str) -> None:
    """Make Home Assistant load the card the way every custom card is loaded: as a dashboard resource.

    A resource is loaded before the dashboard is drawn, so `custom:vigil-card` always exists (a module that is added
    as an "extra module" is loaded next to the dashboard, and a slow load gave "Custom element doesn't exist").
    The resource is made, or moved to the new address after an update, once. A dashboard in YAML mode has resources
    in its own file; there the card is added as an extra module instead, and the documentation says to add it there."""
    resources = getattr(hass.data.get(LOVELACE_DATA), "resources", None)
    if not isinstance(resources, ResourceStorageCollection):
        frontend.add_extra_js_url(hass, url)
        return
    try:
        if not resources.loaded:
            await resources.async_load()
            resources.loaded = True
        ours = [i for i in resources.async_items() if str(i.get("url", "")).split("?")[0] == CARD_URL]
        if not ours:
            await resources.async_create_item({"res_type": "module", "url": url})
            return
        first, *others = ours
        if first.get("url") != url or first.get("type") != "module":
            await resources.async_update_item(first["id"], {"res_type": "module", "url": url})
        for item in others:  # a second copy would load the card twice
            await resources.async_delete_item(item["id"])
    except Exception:  # noqa: BLE001 - the card is not worth a failed setup
        _LOGGER.warning("Could not register the Vigil card as a dashboard resource; add %s as a JavaScript module", CARD_URL)
        frontend.add_extra_js_url(hass, url)


async def _async_remove_card(hass: HomeAssistant) -> None:
    resources = getattr(hass.data.get(LOVELACE_DATA), "resources", None)
    if isinstance(resources, ResourceStorageCollection):
        for item in list(resources.async_items()):
            if str(item.get("url", "")).split("?")[0] == CARD_URL:
                await resources.async_delete_item(item["id"])


async def async_register_panel(hass: HomeAssistant, version: str) -> None:
    if hass.data.get(_DATA_KEY):
        return
    version = await hass.async_add_executor_job(_asset_version, version)
    if not hass.data.get(_STATIC_KEY):
        path = Path(__file__).parent / "frontend" / "vigil-panel.js"
        await hass.http.async_register_static_paths(
            [
                StaticPathConfig(STATIC_URL, str(path), cache_headers=False),
                StaticPathConfig(TEXTS_URL, str(Path(__file__).parent / "frontend" / "texts"), cache_headers=False),
                StaticPathConfig(PARTS_URL, str(Path(__file__).parent / "frontend" / "panel"), cache_headers=False),
                StaticPathConfig(CARD_URL, str(Path(__file__).parent / "frontend" / "vigil-card.js"), cache_headers=False),
                StaticPathConfig(LOGO_URL, str(Path(__file__).parent / "brand" / "icon@2x.png"), cache_headers=True),
            ]
        )
        hass.data[_STATIC_KEY] = True
        await _async_register_card(hass, f"{CARD_URL}?v={version}")
    await panel_custom.async_register_panel(
        hass,
        frontend_url_path=PANEL_URL,
        webcomponent_name="vigil-panel",
        sidebar_title="Vigil Alarm",
        sidebar_icon="mdi:shield-home",
        module_url=f"{STATIC_URL}?v={version}",
        require_admin=True,
        embed_iframe=False,
    )
    hass.data[_DATA_KEY] = True


async def async_remove_panel(hass: HomeAssistant) -> None:
    if hass.data.pop(_DATA_KEY, None):
        frontend.async_remove_panel(hass, PANEL_URL)
    await _async_remove_card(hass)

