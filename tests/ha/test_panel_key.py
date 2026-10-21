"""The panel key: an ESPHome panel that has one must send it with every call, so a call that only *says* it comes
from the panel (the `source` is plain text) is refused."""

from __future__ import annotations

import pytest
from homeassistant.auth.const import GROUP_ID_USER
from homeassistant.core import Context
from custom_components.vigil_alarm.errors import VigilError as ServiceValidationError

from custom_components.vigil_alarm.const import DOMAIN
from custom_components.vigil_alarm.items import items_of

from .common import EVENTS, PANEL
from .test_panels import _client, _house, _ws, panel_item


async def _make_key(hass, hass_ws_client, *panels):
    entry, client = await _client(hass, hass_ws_client, *panels)
    res = await _ws(client, type="vigil_alarm/panel_key", subentry_id="p_garage", action="create")
    assert res["success"], res
    return entry, client, res["result"]["key"]


async def _call(hass, service, **data):
    await hass.services.async_call(DOMAIN, service, data, blocking=True)


async def test_a_panel_without_a_key_works_as_before_and_is_advised_to_get_one(hass):
    entry = await _house(hass, panel_item())
    await _call(hass, "arm", mode="home", code="1234", source="garage")
    assert hass.states.get(PANEL).state == "armed_home"
    assert [p["code"] for p in entry.runtime_data.panels.problems()] == ["panel_no_key"]


async def test_the_key_is_shown_once_only_its_digest_is_kept_and_it_is_not_in_what_the_panel_gets(hass, hass_ws_client):
    entry, client, key = await _make_key(hass, hass_ws_client, panel_item())
    assert len(key) == 32
    stored = items_of(entry)["p_garage"].data
    assert key not in str(dict(stored)) and stored["key_hash"] and stored["key_hash"] != key
    snapshot = (await _ws(client, type="vigil_alarm/get"))["result"]
    panel = next(p for p in snapshot["items"]["panel"] if p["id"] == "p_garage")
    assert panel["has_key"] is True and "key_hash" not in panel["data"] and key not in str(snapshot)
    assert "panel_no_key" not in [p["code"] for p in entry.runtime_data.panels.problems()]
    assert hass.states.get(EVENTS).attributes["event_type"] == "panel_key_created"


async def test_a_call_in_the_name_of_a_panel_with_a_key_needs_the_key(hass, hass_ws_client):
    entry, client, key = await _make_key(hass, hass_ws_client, panel_item())
    with pytest.raises(ServiceValidationError, match="key"):
        await _call(hass, "arm", mode="home", code="1234", source="garage")
    attrs = hass.states.get(EVENTS).attributes
    assert attrs["event_type"] == "panel_refused" and attrs["reason"] == "key" and attrs["source"] == "garage"
    with pytest.raises(ServiceValidationError, match="key"):
        await _call(hass, "arm", mode="home", code="1234", source="garage", key="0" * 32)
    assert hass.states.get(PANEL).state == "disarmed"
    await _call(hass, "arm", mode="home", code="1234", source="garage", key=key)
    assert hass.states.get(PANEL).state == "armed_home" and hass.states.get(PANEL).attributes["changed_via"] == "garage"
    await _call(hass, "disarm", code="1234", source="garage", key=key)
    assert hass.states.get(PANEL).state == "disarmed"


async def test_every_call_a_panel_makes_is_checked(hass, hass_ws_client):
    entry, client, key = await _make_key(hass, hass_ws_client, panel_item())
    await _call(hass, "arm", mode="home", code="1234", source="garage", key=key)
    for service, data in (
        ("disarm", {"code": "1234"}), ("check_code", {"code": "1234"}), ("silence", {"code": "1234"}),
        ("acknowledge", {"code": "1234"}), ("unlock_panel", {"code": "1234", "scope": "sensors"}),
        ("select_partition", {"partition": "main"}), ("clear_alarm_memory", {}),
        ("bypass", {"sensor": "binary_sensor.living_pir", "code": "1234"}),
        ("unbypass", {"sensor": "binary_sensor.living_pir", "code": "1234"}),
    ):
        with pytest.raises(ServiceValidationError, match="key"):
            await _call(hass, service, source="garage", **data)
    assert hass.states.get(PANEL).state == "armed_home"  # none of them got through


async def test_calls_that_do_not_name_the_panel_are_not_touched(hass, hass_ws_client):
    """An automation, a script, the dashboard and the other panels carry no key and need none."""
    entry, client, key = await _make_key(hass, hass_ws_client, panel_item(), panel_item(pid="hall", name="Hall", sid="p_hall"))
    await _call(hass, "arm", mode="home", code="1234")
    await _call(hass, "disarm", code="1234", source="hall")  # another panel, without a key
    await _call(hass, "arm", mode="home", code="1234", source="made up")
    assert hass.states.get(PANEL).state == "armed_home"


async def test_a_new_key_replaces_the_old_one_and_removing_it_ends_the_check(hass, hass_ws_client):
    entry, client, first = await _make_key(hass, hass_ws_client, panel_item())
    second = (await _ws(client, type="vigil_alarm/panel_key", subentry_id="p_garage", action="create"))["result"]["key"]
    assert second != first
    with pytest.raises(ServiceValidationError, match="key"):
        await _call(hass, "check_code", code="1234", source="garage", key=first)
    await _call(hass, "check_code", code="1234", source="garage", key=second)
    res = await _ws(client, type="vigil_alarm/panel_key", subentry_id="p_garage", action="remove")
    assert res["result"] == {"ok": True, "was_set": True}
    assert hass.states.get(EVENTS).attributes["event_type"] == "panel_key_removed"
    await _call(hass, "check_code", code="1234", source="garage")


async def test_editing_the_panel_keeps_its_key(hass, hass_ws_client):
    entry, client, key = await _make_key(hass, hass_ws_client, panel_item())
    res = await _ws(client, type="vigil_alarm/save", kind="panel", subentry_id="p_garage",
                    data={"name": "Garage panel", "panel_id": "garage", "allowed_modes": ["home", "away", "night"], "can_disarm": False})
    assert res["success"] and res["result"].get("ok", True), res
    await _call(hass, "check_code", code="1234", source="garage", key=key)
    with pytest.raises(ServiceValidationError, match="key"):
        await _call(hass, "check_code", code="1234", source="garage")


async def test_a_tablet_has_no_key_and_is_told_apart_by_its_user(hass, hass_ws_client):
    user = await hass.auth.async_create_user("Hall tablet", group_ids=[GROUP_ID_USER])
    entry, client = await _client(hass, hass_ws_client, panel_item(pid="hall-tablet", name="Hall tablet", sid="p_tab", admin_code=None, ha_user=user.id))
    res = await _ws(client, type="vigil_alarm/panel_key", subentry_id="p_tab", action="create")
    assert not res["success"]  # a tablet has no key
    await hass.services.async_call(DOMAIN, "arm", {"mode": "home", "code": "1234"}, blocking=True, context=Context(user_id=user.id))
    assert hass.states.get(PANEL).state == "armed_home"
    assert "panel_no_key" not in [p["code"] for p in entry.runtime_data.panels.problems()]
