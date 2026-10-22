"""A tablet is a panel bound to a Home Assistant user: the profile is enforced on who is calling, not on a text."""

from __future__ import annotations

import pytest
from homeassistant.auth.const import GROUP_ID_ADMIN, GROUP_ID_USER
from homeassistant.core import Context
from custom_components.vigil_alarm.errors import VigilError as ServiceValidationError

from custom_components.vigil_alarm.const import DOMAIN
from custom_components.vigil_alarm.manager import VigilManager

from .common import EVENTS, PANEL
from .test_panels import _client, _house, _ws, panel_item, profile


async def _tablet_user(hass, name="Hall tablet"):
    return await hass.auth.async_create_user(name, group_ids=[GROUP_ID_USER])


def tablet(user, **data):
    return panel_item(pid="hall-tablet", name="Hall tablet", sid="p_tab", admin_code=None, ha_user=user.id, **data)


async def _as(hass, user, service, **data):
    await hass.services.async_call(DOMAIN, service, data, blocking=True, context=Context(user_id=user.id))


async def test_the_profile_is_enforced_on_the_user_whatever_source_the_call_claims(hass):
    user = await _tablet_user(hass)
    await _house(hass, tablet(user, allowed_modes=["home"], can_disarm=False))
    for source in ("hall-tablet", "phone", None):
        kw = {"source": source} if source else {}
        with pytest.raises(ServiceValidationError, match="may not do this"):
            await _as(hass, user, "arm", mode="away", code="1234", **kw)
        attrs = hass.states.get(EVENTS).attributes
        assert attrs["event_type"] == "panel_refused" and attrs["source"] == "hall-tablet"
    await _as(hass, user, "arm", mode="home", code="1234", source="made up")
    assert hass.states.get(PANEL).state == "armed_home"
    assert hass.states.get(PANEL).attributes["changed_by"] == "Anna"
    assert hass.states.get(PANEL).attributes["changed_via"] == "hall-tablet"
    with pytest.raises(ServiceValidationError, match="may not do this"):
        await _as(hass, user, "disarm", code="1234")
    await hass.services.async_call(DOMAIN, "disarm", {"code": "1234", "source": "phone"}, blocking=True)  # another caller
    assert hass.states.get(PANEL).state == "disarmed"


async def test_the_standard_alarm_card_is_enforced_too(hass):
    user = await _tablet_user(hass)
    await _house(hass, tablet(user, allowed_modes=["home"]))
    ctx = Context(user_id=user.id)
    await hass.services.async_call("alarm_control_panel", "alarm_arm_home", {"entity_id": PANEL, "code": "1234"},
                                   blocking=True, context=ctx)
    assert hass.states.get(PANEL).attributes["changed_by"] == "Anna"
    assert hass.states.get(PANEL).attributes["changed_via"] == "hall-tablet"
    await hass.services.async_call("alarm_control_panel", "alarm_disarm", {"entity_id": PANEL, "code": "1234"},
                                   blocking=True, context=ctx)
    with pytest.raises(ServiceValidationError, match="may not do this"):
        await hass.services.async_call("alarm_control_panel", "alarm_arm_away", {"entity_id": PANEL, "code": "1234"},
                                       blocking=True, context=ctx)


async def test_the_tablet_has_its_own_lockout_timer_whatever_source_it_claims(hass, monkeypatch):
    user = await _tablet_user(hass)
    entry = await _house(hass, tablet(user))
    clock = [1000.0]
    monkeypatch.setattr(VigilManager, "_clock", staticmethod(lambda: clock[0]))
    for i in range(3):
        with pytest.raises(ServiceValidationError, match="Invalid code|Too many wrong codes"):
            await _as(hass, user, "disarm", code="0000", source=f"name {i}")  # changing the name does not help
    assert set(entry.runtime_data.lockout.status()) == {"hall-tablet"}
    with pytest.raises(ServiceValidationError, match="Too many wrong codes"):
        await _as(hass, user, "arm", mode="home", code="1234")
    await hass.services.async_call(DOMAIN, "arm", {"mode": "home", "code": "1234", "source": "phone"}, blocking=True)


async def test_a_tablet_is_never_an_administrator_for_vigil(hass):
    user = await _tablet_user(hass)
    await _house(hass, tablet(user), code_arm_required=False)
    with pytest.raises(ServiceValidationError, match="code is required"):  # bypass from a panel always needs a code
        await _as(hass, user, "bypass", sensor="binary_sensor.front_door")
    assert hass.states.async_entity_ids("switch") == []  # and there is no switch to get round it


async def test_a_blocked_tablet_is_refused(hass):
    user = await _tablet_user(hass)
    await _house(hass, tablet(user, blocked=True))
    with pytest.raises(ServiceValidationError, match="is blocked"):
        await _as(hass, user, "arm", mode="home", code="1234")


async def test_the_profile_of_a_tablet_says_so_and_a_tablet_is_not_watched_for_offline(hass, freezer):
    from datetime import timedelta

    from homeassistant.helpers import issue_registry as ir
    from homeassistant.util import dt as dt_util
    from pytest_homeassistant_custom_component.common import async_fire_time_changed

    user = await _tablet_user(hass)
    entry = await _house(hass, tablet(user))
    assert profile(hass, "sensor.hall_tablet_profile").attributes["kind"] == "tablet"
    freezer.tick(timedelta(seconds=1800))
    async_fire_time_changed(hass, dt_util.utcnow())
    await hass.async_block_till_done()
    assert not [i for i in ir.async_get(hass).issues if "panel_offline" in i[1]]
    status = entry.runtime_data.panels.status()[0]
    assert status["kind"] == "tablet" and status["connected"] is None and status["offline"] is False


async def test_a_tablet_unlocks_with_its_administrator_code_whatever_source_it_sends(hass):
    from .test_panels import panel_item as item

    user = await _tablet_user(hass)
    await _house(hass, item(pid="hall-tablet", name="Hall tablet", sid="p_tab", admin_code="9999", ha_user=user.id))
    await _as(hass, user, "unlock_panel", code="9999", source="whatever")
    assert profile(hass, "sensor.hall_tablet_profile").attributes["unlocked"] is True


async def test_choosing_the_user_of_a_tablet(hass, hass_ws_client):
    from custom_components.vigil_alarm.items import items_of

    ok_user = await _tablet_user(hass)
    admin = await hass.auth.async_create_user("Boss", group_ids=[GROUP_ID_ADMIN])
    entry, client = await _client(hass, hass_ws_client)
    got = (await _ws(client, type="vigil_alarm/get"))["result"]
    names = {u["name"] for u in got["ha_users"]}
    assert "Hall tablet" in names and "Boss (admin)" in names  # an administrator may be chosen, a system user not
    assert all(u["name"] != "Home Assistant Content" for u in got["ha_users"])
    for user_id, error in (("nobody", "ha_user_unknown"),):
        res = await _ws(client, type="vigil_alarm/save", kind="panel",
                        data={"name": "T", "panel_id": "t1", "ha_user": user_id})
        assert res["result"]["errors"] == {"ha_user": error}
    res = await _ws(client, type="vigil_alarm/save", kind="panel", data={"name": "T", "panel_id": "t1", "ha_user": ok_user.id})
    assert res["result"]["ok"] is True
    await hass.async_block_till_done()
    res = await _ws(client, type="vigil_alarm/save", kind="panel", data={"name": "T2", "panel_id": "t2", "ha_user": ok_user.id})
    assert res["result"]["errors"] == {"ha_user": "ha_user_in_use"}
    assert any(i.data.get("ha_user") == ok_user.id for i in items_of(entry).values())


# ------------------------------------------------------------------------- the Vigil card

async def _user_client(hass, hass_ws_client, user):
    refresh = await hass.auth.async_create_refresh_token(user, "https://example.test/")
    return await hass_ws_client(hass, hass.auth.async_create_access_token(refresh))


async def test_the_card_asks_which_panel_belongs_to_the_logged_in_user(hass, hass_ws_client):
    user = await _tablet_user(hass)
    entry = await _house(hass, tablet(user))
    client = await _user_client(hass, hass_ws_client, user)  # not an administrator: still allowed
    got = (await _ws(client, type="vigil_alarm/tablet"))["result"]
    assert got == {"linked": True, "kind": "tablet", "user": "Hall tablet", "panel_id": "hall-tablet", "name": "Hall tablet",
                   "profile_entity": "sensor.hall_tablet_profile", "alarm_entity": PANEL,
                   "partitions": [{"id": "main", "name": "Home", "alarm": PANEL, "modes": ["home", "away", "night"]}],
                   "all_entity": None, "default_partition": "main", "return_seconds": 30, "partition_total": 1}
    assert hass.states.get(got["profile_entity"]) is not None
    assert entry.runtime_data.panels.status()[0]["card"] is True


async def test_a_user_without_a_panel_gets_nothing_to_go_on(hass, hass_ws_client):
    user = await _tablet_user(hass)
    other = await hass.auth.async_create_user("Other", group_ids=[GROUP_ID_USER])
    entry = await _house(hass, tablet(user))
    client = await _user_client(hass, hass_ws_client, other)
    assert (await _ws(client, type="vigil_alarm/tablet"))["result"] == {"linked": False, "user": "Other"}
    admin = await hass_ws_client(hass)
    assert (await _ws(admin, type="vigil_alarm/tablet"))["result"]["linked"] is False  # an administrator is no tablet
    assert entry.runtime_data.panels.status()[0]["card"] is False


async def test_the_administrator_commands_stay_closed_to_a_tablet_user(hass, hass_ws_client):
    user = await _tablet_user(hass)
    await _house(hass, tablet(user))
    client = await _user_client(hass, hass_ws_client, user)
    res = await _ws(client, type="vigil_alarm/get")
    assert res["success"] is False and res["error"]["code"] == "unauthorized"


async def test_a_tablet_whose_card_goes_quiet_is_reported_after_ten_minutes(hass, hass_ws_client, freezer):
    from datetime import timedelta

    from homeassistant.helpers import issue_registry as ir
    from homeassistant.util import dt as dt_util
    from pytest_homeassistant_custom_component.common import async_fire_time_changed

    from custom_components.vigil_alarm.const import PANEL_OFFLINE_SECONDS

    async def tick(seconds):
        freezer.tick(timedelta(seconds=seconds))
        async_fire_time_changed(hass, dt_util.utcnow())
        await hass.async_block_till_done()

    def offline():
        return [i for i in ir.async_get(hass).issues if "panel_offline" in i[1]]

    user = await _tablet_user(hass)
    entry = await _house(hass, tablet(user))
    await tick(PANEL_OFFLINE_SECONDS + 120)
    assert not offline()  # no card has said hello: nothing to watch (Home Assistant's own card cannot)
    async def hello():  # a new connection each time: a frozen clock would time the old one out
        await _ws(await _user_client(hass, hass_ws_client, user), type="vigil_alarm/tablet")

    await hello()
    await tick(PANEL_OFFLINE_SECONDS - 60)
    assert not offline()
    await tick(120)
    assert offline() and entry.runtime_data.panels.status()[0]["offline"] is True
    assert hass.states.get(PANEL).state == "disarmed"  # an offline tablet never changes the alarm
    await hello()  # it is back
    await tick(31)
    assert not offline() and entry.runtime_data.panels.status()[0]["connected"] is True


async def test_a_tablet_that_used_the_card_is_still_watched_after_a_restart(hass, hass_ws_client, freezer):
    from datetime import timedelta

    from homeassistant.helpers import issue_registry as ir
    from homeassistant.util import dt as dt_util
    from pytest_homeassistant_custom_component.common import async_fire_time_changed

    from custom_components.vigil_alarm.const import PANEL_OFFLINE_SECONDS

    user = await _tablet_user(hass)
    entry = await _house(hass, tablet(user))
    client = await _user_client(hass, hass_ws_client, user)
    await _ws(client, type="vigil_alarm/tablet")
    await entry.runtime_data.panels.async_flush()
    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.runtime_data.panels.status()[0]["card"] is True  # remembered
    freezer.tick(timedelta(seconds=PANEL_OFFLINE_SECONDS + 60))
    async_fire_time_changed(hass, dt_util.utcnow())
    await hass.async_block_till_done()
    assert [i for i in ir.async_get(hass).issues if "panel_offline" in i[1]]


# ---- the list of accounts: a tablet and a phone are the same thing, and everybody else is refused ------------

async def _ordinary(hass, name):
    if not hass.auth._store._users:  # the very first account of a test instance is the owner, an administrator
        await hass.auth.async_create_user("Owner", group_ids=[GROUP_ID_ADMIN])
    return await hass.auth.async_create_user(name, group_ids=[GROUP_ID_USER])


async def test_a_phone_is_registered_like_a_tablet_and_any_valid_code_works_on_it(hass):
    phone = await _ordinary(hass, "Cleo's phone")
    await _house(hass, panel_item(pid="cleo-phone", name="Cleo's phone", sid="p_ph", admin_code=None, ha_user=phone.id))
    await _as(hass, phone, "arm", mode="home", code="5678")  # Bob's code, on Cleo's phone
    assert hass.states.get(PANEL).attributes["changed_by"] == "Bob"
    assert hass.states.get(PANEL).attributes["changed_via"] == "cleo-phone"
    with pytest.raises(ServiceValidationError, match="code is required"):
        await _as(hass, phone, "disarm")  # no code, no operation
    await _as(hass, phone, "disarm", code="1234")


async def test_once_an_account_is_registered_other_ordinary_accounts_are_refused_before_the_code(hass):
    phone = await _ordinary(hass, "Cleo's phone")
    kid = await _ordinary(hass, "Kid")
    boss = await hass.auth.async_create_user("Boss", group_ids=[GROUP_ID_ADMIN])
    entry = await _house(hass, tablet(phone))
    for _ in range(6):  # a refused account cannot be used to lock anything
        with pytest.raises(ServiceValidationError, match="not registered"):
            await _as(hass, kid, "disarm", code="0000")
    attrs = hass.states.get(EVENTS).attributes
    assert attrs["event_type"] == "user_refused" and attrs["user"] == "Kid" and attrs["action"] == "disarm"
    assert entry.runtime_data.lockout.status() == {}
    with pytest.raises(ServiceValidationError, match="not registered"):
        await hass.services.async_call("alarm_control_panel", "alarm_disarm", {"entity_id": PANEL, "code": "1234"},
                                       blocking=True, context=Context(user_id=kid.id))
    await _as(hass, boss, "arm", mode="home", code="1234")  # an administrator is outside the rule
    await hass.services.async_call(DOMAIN, "disarm", {"code": "1234"}, blocking=True)  # and so is an automation
    await _as(hass, phone, "arm", mode="home", code="1234")  # the registered account works
    assert hass.states.get(PANEL).state == "armed_home"


async def test_without_a_registered_account_nothing_changes(hass):
    kid = await _ordinary(hass, "Kid")
    await _house(hass, panel_item())  # an ESPHome panel only
    await _as(hass, kid, "arm", mode="home", code="1234")
    assert hass.states.get(PANEL).state == "armed_home"


async def test_a_wrong_code_on_one_account_locks_only_that_account(hass):
    phone = await _ordinary(hass, "Cleo's phone")
    tab_user = await _tablet_user(hass)
    await _house(hass, tablet(tab_user),
                 panel_item(pid="cleo-phone", name="Cleo's phone", sid="p_ph", admin_code=None, ha_user=phone.id))
    for _ in range(3):
        with pytest.raises(ServiceValidationError, match="Invalid code|Too many wrong codes"):
            await _as(hass, phone, "arm", mode="home", code="0000")
    with pytest.raises(ServiceValidationError, match="Too many wrong codes"):
        await _as(hass, phone, "arm", mode="home", code="1234")
    await _as(hass, tab_user, "arm", mode="home", code="1234")
    assert hass.states.get(PANEL).state == "armed_home"


# ---- the form: an ESPHome panel and a tablet or phone each get only the questions that fit ---------------------

async def test_a_tablet_or_phone_is_added_without_a_panel_id_and_gets_one_from_its_name(hass, hass_ws_client):
    from custom_components.vigil_alarm.items import items_of

    phone = await _ordinary(hass, "Cleo's phone")
    other = await _ordinary(hass, "Other")
    entry, client = await _client(hass, hass_ws_client)
    first = await _ws(client, type="vigil_alarm/save", kind="panel",
                      data={"name": "Cleo's phone", "device": "account", "ha_user": phone.id})
    assert first["result"]["ok"] is True
    again = await _ws(client, type="vigil_alarm/save", kind="panel",
                      data={"name": "Cleo's  Phone!", "device": "account", "ha_user": other.id})
    assert again["result"]["ok"] is True
    ids = sorted(i.data["panel_id"] for i in items_of(entry).values() if i.subentry_type == "panel")
    assert ids == ["cleo-s-phone", "cleo-s-phone-2"]  # lower case, dashes, and never twice
    saved = next(i for i in items_of(entry).values() if i.subentry_type == "panel" and i.data["panel_id"] == "cleo-s-phone")
    assert saved.data["ha_user"] == phone.id
    # editing keeps the panel id, also when the name changes
    res = await _ws(client, type="vigil_alarm/save", kind="panel", subentry_id=saved.subentry_id,
                    data={"name": "Cleo", "device": "account", "ha_user": phone.id})
    assert res["result"]["ok"] is True
    assert items_of(entry)[saved.subentry_id].data["panel_id"] == "cleo-s-phone"


async def test_a_tablet_needs_an_account_and_an_esphome_panel_needs_a_panel_id(hass, hass_ws_client):
    _entry, client = await _client(hass, hass_ws_client)
    res = await _ws(client, type="vigil_alarm/save", kind="panel", data={"name": "Wall", "device": "account"})
    assert res["result"]["errors"] == {"ha_user": "required"}
    res = await _ws(client, type="vigil_alarm/save", kind="panel", data={"name": "Wall", "device": "esphome"})
    assert res["result"]["errors"] == {"panel_id": "required"}
    res = await _ws(client, type="vigil_alarm/save", kind="panel",
                    data={"name": "Wall", "device": "esphome", "panel_id": "wall", "ha_user": "nobody"})
    assert res["result"]["ok"] is True  # an account is not asked for an ESPHome panel, so it is not kept


async def test_an_administrator_chosen_as_the_account_of_a_device_gets_no_administrator_shortcuts(hass, hass_ws_client):
    boss = await hass.auth.async_create_user("Boss", group_ids=[GROUP_ID_ADMIN])
    entry, client = await _client(hass, hass_ws_client)
    res = await _ws(client, type="vigil_alarm/save", kind="panel",
                    data={"name": "Boss tablet", "device": "account", "ha_user": boss.id})
    assert res["result"]["ok"] is True
    await hass.async_block_till_done()
    # on the device a code is needed to bypass, which an administrator in the UI would not need
    with pytest.raises(ServiceValidationError, match="code is required"):
        await _as(hass, boss, "bypass", sensor="binary_sensor.front_door")
    await _as(hass, boss, "bypass", sensor="binary_sensor.front_door", code="1234")
