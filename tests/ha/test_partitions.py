"""Release 0.6.0: partitions. Each part of the house has its own state; safety sensors are for the whole house."""

from __future__ import annotations

import pytest
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import async_mock_service

from custom_components.vigil_alarm.const import DOMAIN

from .common import EVENTS, make_entry, sub
from .test_integration import _setup, _tick

GARAGE = sub("partition", "Garage", {"modes": ["away"], "exit_delay_away": 0, "default_entry_delay": 0}, "p_gar")
GARAGE_GROUP = sub("sensor_group", "Garage away", {"modes": ["away"], "partition": "p_gar"}, "g_gar")
GARAGE_DOOR = sub("zone", "Garage door", {"entity_id": "binary_sensor.garage_door", "cls": "intrusion",
                  "type": "instant", "sensor_groups": ["g_gar"], "partition": "p_gar"}, "gdoor")
EXTRA = (GARAGE, GARAGE_GROUP, GARAGE_DOOR)


def ids(hass, entry):
    reg = er.async_get(hass)
    get = lambda uid: reg.async_get_entity_id("alarm_control_panel", DOMAIN, uid)  # noqa: E731
    return get(entry.entry_id), get(f"{entry.entry_id}_partition_p_gar"), get(f"{entry.entry_id}_all")


async def house(hass, *extra, **data):
    hass.states.async_set("binary_sensor.garage_door", "off")
    entry = await _setup(hass, make_entry(extra_subentries=list(EXTRA) + list(extra), **data))
    return entry, *ids(hass, entry)


async def act(hass, entity, service, **data):
    await hass.services.async_call("alarm_control_panel", service, {"entity_id": entity, **data}, blocking=True)


async def test_every_partition_has_an_entity_and_there_is_one_for_all(hass):
    entry, home, garage, everything = await house(hass)
    assert home and garage and everything
    assert hass.states.get(everything).state == "disarmed"
    assert hass.states.get(garage).attributes["partition"] == "p_gar"
    assert hass.states.get(garage).attributes["partition_name"] == "Garage"
    assert hass.states.get(garage).attributes["supported_features"] == 2  # away only


async def test_one_partition_has_no_all_entity(hass):
    entry = await _setup(hass, make_entry())
    assert ids(hass, entry)[1:] == (None, None)


async def test_the_garage_arms_without_the_house(hass):
    entry, home, garage, everything = await house(hass)
    await act(hass, garage, "alarm_arm_away", code="1234")
    assert hass.states.get(garage).state == "armed_away"
    assert hass.states.get(home).state == "disarmed"
    assert hass.states.get(everything).state == "armed_away"
    assert hass.states.get(everything).attributes["status"] == "mixed"
    assert hass.states.get(everything).attributes["partitions"] == {"Home": "disarmed", "Garage": "armed_away"}


async def test_an_intrusion_in_the_garage_triggers_only_the_garage(hass):
    entry, home, garage, everything = await house(hass)
    await act(hass, garage, "alarm_arm_away", code="1234")
    hass.states.async_set("binary_sensor.garage_door", "on")
    await hass.async_block_till_done()
    assert hass.states.get(garage).state == "triggered"
    assert hass.states.get(home).state == "disarmed"
    assert hass.states.get(everything).state == "triggered"
    assert hass.states.get(EVENTS).attributes["partition"] == "p_gar"
    assert hass.states.get(EVENTS).attributes["partition_name"] == "Garage"


async def test_the_house_sensors_do_not_watch_the_garage(hass):
    entry, home, garage, everything = await house(hass)
    await act(hass, garage, "alarm_arm_away", code="1234")
    hass.states.async_set("binary_sensor.living_pir", "on")  # a sensor of the house
    await hass.async_block_till_done()
    assert hass.states.get(garage).state == "armed_away"


async def test_arm_all_arms_every_partition_in_the_same_mode(hass, freezer):
    entry, home, garage, everything = await house(hass)
    await act(hass, everything, "alarm_arm_away", code="1234")
    assert hass.states.get(home).state == "arming" and hass.states.get(garage).state == "armed_away"
    assert hass.states.get(everything).state == "arming"
    await _tick(hass, freezer, 61)
    assert hass.states.get(everything).state == "armed_away"
    assert hass.states.get(everything).attributes["status"] == "armed_away"
    await act(hass, everything, "alarm_disarm", code="1234")
    assert hass.states.get(home).state == hass.states.get(garage).state == "disarmed"


async def test_arm_all_leaves_a_partition_without_the_mode_alone(hass, freezer):
    entry, home, garage, everything = await house(hass)
    await act(hass, everything, "alarm_arm_home", code="1234")  # the garage has no home mode
    assert hass.states.get(home).state == "armed_home"
    assert hass.states.get(garage).state == "disarmed"


async def test_arm_all_arms_nothing_when_one_partition_cannot(hass):
    side = sub("zone", "Garage side", {"entity_id": "binary_sensor.garage_side", "cls": "intrusion", "type": "instant",
               "sensor_groups": ["g_gar"], "partition": "p_gar", "at_arm_open": "refuse"}, "gside")
    hass.states.async_set("binary_sensor.garage_side", "on")  # open, and it refuses
    entry, home, garage, everything = await house(hass, side)
    with pytest.raises(ServiceValidationError, match="Arming refused"):
        await act(hass, everything, "alarm_arm_away", code="1234")
    assert hass.states.get(home).state == hass.states.get(garage).state == "disarmed"
    hass.states.async_set("binary_sensor.garage_side", "off")
    await hass.async_block_till_done()
    await act(hass, everything, "alarm_arm_away", code="1234")
    assert hass.states.get(garage).state == "armed_away"


async def test_the_arm_service_takes_a_partition(hass):
    entry, home, garage, everything = await house(hass)
    await hass.services.async_call("vigil_alarm", "arm", {"mode": "away", "code": "1234", "partition": "p_gar"}, blocking=True)
    assert hass.states.get(garage).state == "armed_away" and hass.states.get(home).state == "disarmed"
    await hass.services.async_call("vigil_alarm", "disarm", {"code": "1234", "partition": "p_gar"}, blocking=True)
    assert hass.states.get(garage).state == "disarmed"
    with pytest.raises(ServiceValidationError, match="Unknown partition"):
        await hass.services.async_call("vigil_alarm", "arm", {"mode": "away", "code": "1234", "partition": "nope"}, blocking=True)


async def test_fire_is_one_alarm_for_the_whole_house(hass):
    entry, home, garage, everything = await house(hass)
    seen = []
    from homeassistant.core import callback
    from homeassistant.helpers.dispatcher import async_dispatcher_connect
    from custom_components.vigil_alarm.manager import SIGNAL_EVENT
    async_dispatcher_connect(hass, SIGNAL_EVENT.format(entry.entry_id), callback(lambda e: seen.append(e)))
    hass.states.async_set("binary_sensor.smoke", "on")
    await hass.async_block_till_done()
    assert hass.states.get(home).state == hass.states.get(garage).state == "triggered"
    assert [e["type"] for e in seen].count("triggered") == 1  # one alarm, one message
    assert [e["partition"] for e in seen if e["type"] == "triggered"] == ["main"]
    # disarming the garage ends it in every partition that is in it
    hass.states.async_set("binary_sensor.smoke", "off")
    await hass.async_block_till_done()
    await act(hass, garage, "alarm_disarm", code="1234")
    assert hass.states.get(home).state == hass.states.get(garage).state == "disarmed"
    assert [e["type"] for e in seen].count("trigger_ended") == 1


async def test_a_user_can_be_limited_to_partitions(hass):
    from .common import user_data
    limited = sub("user", "Carl", user_data("4321", allowed_modes=[], partitions=["main"]), "carl")
    entry, home, garage, everything = await house(hass, limited)
    with pytest.raises(ServiceValidationError, match="Carl may not use partition Garage"):
        await act(hass, garage, "alarm_arm_away", code="4321")
    await act(hass, home, "alarm_arm_home", code="4321")
    assert hass.states.get(home).state == "armed_home"
    await act(hass, everything, "alarm_disarm", code="4321")  # "all" is limited to what he may use
    assert hass.states.get(home).state == "disarmed"


async def test_a_panel_can_be_limited_to_partitions(hass):
    panel = sub("panel", "Garage panel", {"panel_id": "garage-panel", "partitions": ["p_gar"], "can_disarm": True,
                                          "can_bypass": True, "can_silence": True, "allowed_modes": []}, "pp")
    entry, home, garage, everything = await house(hass, panel)
    with pytest.raises(ServiceValidationError, match="may not do this"):
        await hass.services.async_call("vigil_alarm", "arm", {"mode": "home", "code": "1234", "source": "garage-panel",
                                                               "partition": "main"}, blocking=True)
    profile = entry.runtime_data.panels.profile(entry.runtime_data.panels.get("garage-panel"))
    assert [p["id"] for p in profile["partitions"]] == ["p_gar"]
    assert profile["alarm"] == [garage]  # a firmware from before partitions uses the first one it may use
    assert profile["allowed_modes"] == ["away"]


async def test_sirens_follow_their_partitions_but_fire_sounds_everywhere(hass):
    from .test_sirens import siren
    hass.states.async_set("switch.garage_siren", "off")
    hass.states.async_set("switch.house_siren", "off")
    garage_siren = siren("s_gar", "Garage siren", control="switch.garage_siren", partitions=["p_gar"])
    house_siren = siren("s_house", "House siren", control="switch.house_siren", partitions=["main"])
    entry, home, garage, everything = await house(hass, garage_siren, house_siren)
    on = async_mock_service(hass, "switch", "turn_on")  # after the set-up: the real services are registered there
    async_mock_service(hass, "switch", "turn_off")
    await act(hass, garage, "alarm_arm_away", code="1234")
    hass.states.async_set("binary_sensor.garage_door", "on")
    await hass.async_block_till_done()
    assert [c.data["entity_id"] for c in on] == ["switch.garage_siren"]
    await act(hass, garage, "alarm_disarm", code="1234")
    on.clear()
    hass.states.async_set("binary_sensor.smoke", "on")
    await hass.async_block_till_done()
    assert sorted(c.data["entity_id"] for c in on) == ["switch.garage_siren", "switch.house_siren"]


async def test_a_siren_stays_on_while_another_partition_it_serves_is_still_in_alarm(hass, freezer):
    from .test_sirens import siren
    hass.states.async_set("switch.siren", "off")
    entry, home, garage, everything = await house(hass, siren())
    on = async_mock_service(hass, "switch", "turn_on")
    off = async_mock_service(hass, "switch", "turn_off")
    await act(hass, home, "alarm_arm_home", code="1234")
    await act(hass, garage, "alarm_arm_away", code="1234")
    hass.states.async_set("binary_sensor.front_door", "on")  # the house: entry delay, then the alarm
    await hass.async_block_till_done()
    await _tick(hass, freezer, 31)
    hass.states.async_set("binary_sensor.garage_door", "on")
    await hass.async_block_till_done()
    assert hass.states.get(home).state == hass.states.get(garage).state == "triggered"
    await act(hass, garage, "alarm_disarm", code="1234")
    await hass.async_block_till_done()
    assert hass.states.get(garage).state == "disarmed" and hass.states.get(home).state == "triggered"
    assert not off, "the siren belongs to the house alarm too: it keeps sounding"
    await act(hass, home, "alarm_disarm", code="1234")
    await hass.async_block_till_done()
    assert off


async def test_channels_follow_their_partitions(hass):
    from .test_notifications import channel
    calls = async_mock_service(hass, "notify", "mobile_app_anna")
    other = async_mock_service(hass, "notify", "mobile_app_bob")
    c1 = sub("notification", "Anna", {"service": "mobile_app_anna", "categories": ["alarm", "arming"], "delay": 0,
                                      "priority": False, "partitions": ["p_gar"]}, "n1")
    c2 = sub("notification", "Bob", {"service": "mobile_app_bob", "categories": ["alarm", "arming"], "delay": 0,
                                     "priority": False, "partitions": ["main"]}, "n2")
    entry, home, garage, everything = await house(hass, c1, c2)
    await act(hass, garage, "alarm_arm_away", code="1234")
    assert [c.data["message"] for c in calls] == ["Armed (away) by Anna [Garage]"]
    assert other == []
    hass.states.async_set("binary_sensor.smoke", "on")  # fire: both channels, once
    await hass.async_block_till_done()
    assert len(calls) == 2 and len(other) == 1


async def test_the_state_is_kept_per_partition_over_a_restart(hass):
    entry, home, garage, everything = await house(hass)
    await act(hass, garage, "alarm_arm_away", code="1234")
    manager = entry.runtime_data
    saved = manager._data_to_save()
    assert set(saved["partitions"]) == {"main", "p_gar"}
    assert await hass.config_entries.async_unload(entry.entry_id)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get(garage).state == "armed_away"
    assert hass.states.get(home).state == "disarmed"


async def test_a_state_saved_before_partitions_is_the_first_partition(hass):
    from homeassistant.helpers.storage import Store
    entry = make_entry(extra_subentries=list(EXTRA))
    hass.states.async_set("binary_sensor.garage_door", "off")
    for n in ("front_door", "living_pir", "smoke", "tamper"):
        hass.states.async_set(f"binary_sensor.{n}", "off")
    entry.add_to_hass(hass)
    # the state of one engine, as 0.5.x saved it
    from custom_components.vigil_alarm.vigil_core import Config, Engine
    from custom_components.vigil_alarm.manager import build_config
    engine = Engine(build_config(entry), now=0.0)
    engine.arm("home", user=None)
    store = Store(hass, 1, f"{DOMAIN}.{entry.entry_id}")
    await store.async_save(engine.export_state())
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    home, garage, _all = ids(hass, entry)
    assert hass.states.get(home).state == "armed_home" and hass.states.get(garage).state == "disarmed"


# ---- the admin panel's save, delete and readiness

async def _admin(hass, hass_ws_client, *extra):
    from .test_panel import _client
    hass.states.async_set("binary_sensor.garage_door", "off")
    return await _client(hass, hass_ws_client, make_entry(extra_subentries=list(extra)))


async def test_the_panel_saves_a_partition_and_a_sensor_in_it(hass, hass_ws_client):
    from custom_components.vigil_alarm.items import items_of
    from .test_panel import _ws
    entry, client = await _admin(hass, hass_ws_client)
    res = await _ws(client, type="vigil_alarm/save", kind="partition", data={"name": "Shed", "modes": ["away"]})
    assert res["result"]["ok"] is True, res
    pid = res["result"]["id"]
    await hass.async_block_till_done()
    assert items_of(entry)[pid].subentry_type == "partition"
    res = await _ws(client, type="vigil_alarm/save", kind="sensor_group", data={"name": "Shed away", "modes": ["away"], "partition": pid})
    assert res["result"]["ok"] is True, res
    group = res["result"]["id"]
    await hass.async_block_till_done()
    sensor = {"name": "Shed door", "entity_id": "binary_sensor.shed", "cls": "intrusion", "type": "instant",
              "sensor_groups": [group], "partition": "nope"}
    res = await _ws(client, type="vigil_alarm/save", kind="sensor", data=sensor)
    assert res["result"]["errors"] == {"partition": "unknown_partition"}
    res = await _ws(client, type="vigil_alarm/save", kind="sensor", data={**sensor, "partition": pid})
    assert res["result"]["ok"] is True, res


async def test_a_partition_with_sensors_cannot_be_deleted(hass, hass_ws_client):
    from .test_panel import _ws
    entry, client = await _admin(hass, hass_ws_client, *EXTRA)
    res = await _ws(client, type="vigil_alarm/delete", subentry_id="p_gar")
    assert res["result"]["ok"] is False
    assert "partition_in_use" in str(res["result"])
    # empty it, then it can go
    res = await _ws(client, type="vigil_alarm/delete", subentry_id="gdoor")
    assert res["result"]["ok"] is True
    await hass.async_block_till_done()
    res = await _ws(client, type="vigil_alarm/delete", subentry_id="p_gar")
    assert "partition_has_groups" in str(res["result"])  # its group has to go too
    res = await _ws(client, type="vigil_alarm/delete", subentry_id="g_gar")
    assert res["result"]["ok"] is True
    await hass.async_block_till_done()
    res = await _ws(client, type="vigil_alarm/delete", subentry_id="p_gar")
    assert res["result"]["ok"] is True


async def test_readiness_says_a_partition_without_sensors_watches_nothing(hass, hass_ws_client):
    from .test_panel import _ws
    entry, client = await _admin(hass, hass_ws_client, GARAGE, GARAGE_GROUP)
    res = await _ws(client, type="vigil_alarm/readiness")
    assert "partition_empty" in {f["code"] for f in res["result"]["findings"]}


async def test_a_new_partition_starts_with_the_modes_and_times_of_the_house(hass, hass_ws_client):
    from .test_panel import _ws
    entry, client = await _admin(hass, hass_ws_client)
    res = await _ws(client, type="vigil_alarm/get")
    fields = {f["key"]: f for f in res["result"]["forms"]["partition"]}
    house = res["result"]["entry"]["data"]
    assert fields["modes"]["default"] == house["modes"]
    for mode in ("home", "away", "night", "vacation", "custom"):
        assert fields[f"exit_delay_{mode}"]["default"] == house.get(f"exit_delay_{mode}", fields[f"exit_delay_{mode}"]["default"])
        assert fields[f"exit_delay_{mode}"]["default"] is not None


# ---- sensor groups per partition, and the partition in the log

async def test_a_sensor_group_can_belong_to_a_partition(hass, hass_ws_client):
    from .test_panel import _ws
    entry, client = await _admin(hass, hass_ws_client, GARAGE)
    res = await _ws(client, type="vigil_alarm/save", kind="sensor_group", data={"name": "Garage night", "modes": ["night"], "partition": "p_gar"})
    assert res["result"]["errors"] == {"modes": "no_modes"}  # the garage has only Away
    res = await _ws(client, type="vigil_alarm/save", kind="sensor_group", data={"name": "Garage shell", "modes": ["away"], "partition": "p_gar"})
    assert res["result"]["ok"] is True, res
    gid = res["result"]["id"]
    await hass.async_block_till_done()
    res = await _ws(client, type="vigil_alarm/save", kind="sensor_group", data={"name": "X", "modes": ["away"], "partition": "nope"})
    assert res["result"]["errors"] == {"partition": "unknown_partition"}
    sensor = {"name": "Shed", "entity_id": "binary_sensor.shed", "cls": "intrusion", "type": "instant", "sensor_groups": [gid]}
    # a sensor can only use the groups of its own partition
    res = await _ws(client, type="vigil_alarm/save", kind="sensor", data={**sensor, "partition": "main"})
    assert res["result"]["errors"] == {"sensor_groups": "group_other_partition"}
    assert res["result"]["placeholders"] == {"group": "Garage shell"}
    res = await _ws(client, type="vigil_alarm/save", kind="sensor", data={**sensor, "partition": "p_gar"})
    assert res["result"]["ok"] is True, res
    res = await _ws(client, type="vigil_alarm/save", kind="sensor", data={**sensor, "name": "Shed 2", "entity_id": "binary_sensor.shed2", "sensor_groups": ["g_away"], "partition": "p_gar"})
    assert res["result"]["errors"] == {"sensor_groups": "group_other_partition"}  # g_away is a group of the first partition
    res = await _ws(client, type="vigil_alarm/save", kind="sensor", data={**sensor, "name": "Shed 2", "entity_id": "binary_sensor.shed2", "sensor_groups": ["g_away"], "partition": "main"})
    assert res["result"]["ok"] is True, res
    await hass.async_block_till_done()
    # the group cannot move to the house while a sensor of the garage uses it, and the garage cannot go while it has the group
    res = await _ws(client, type="vigil_alarm/save", kind="sensor_group", subentry_id=gid, data={"name": "Garage shell", "modes": ["away"], "partition": "main"})
    assert res["result"]["errors"] == {"partition": "group_in_use_elsewhere"}
    res = await _ws(client, type="vigil_alarm/delete", subentry_id="p_gar")
    assert "partition_in_use" in str(res["result"])


async def test_a_partition_with_a_sensor_group_cannot_be_deleted(hass, hass_ws_client):
    from .test_panel import _ws
    entry, client = await _admin(hass, hass_ws_client, GARAGE)
    res = await _ws(client, type="vigil_alarm/save", kind="sensor_group", data={"name": "Garage shell", "modes": ["away"], "partition": "p_gar"})
    assert res["result"]["ok"] is True
    await hass.async_block_till_done()
    res = await _ws(client, type="vigil_alarm/delete", subentry_id="p_gar")
    assert "partition_has_groups" in str(res["result"])


async def test_the_log_says_which_partition_an_event_is_about(hass):
    entry, home, garage, everything = await house(hass)
    await act(hass, garage, "alarm_arm_away", code="1234")
    await hass.async_block_till_done()
    armed = [e for e in entry.runtime_data.eventlog.entries if e["event"] == "armed"]
    assert armed and armed[-1]["partition"] == "Garage"


async def test_the_log_column_is_filled_with_one_partition_too(hass):
    entry = await _setup(hass, make_entry())
    await hass.services.async_call("alarm_control_panel", "alarm_arm_home",
                                   {"entity_id": ids(hass, entry)[0], "code": "1234"}, blocking=True)
    await hass.async_block_till_done()
    armed = [e for e in entry.runtime_data.eventlog.entries if e["event"] == "armed"]
    assert armed and armed[-1]["partition"] == "Home"


async def test_the_first_partition_can_be_renamed_with_one_partition(hass, hass_ws_client):
    from .test_panel import _ws
    entry, client = await _admin(hass, hass_ws_client)
    res = await _ws(client, type="vigil_alarm/get")
    assert [(p["id"], p["primary"]) for p in res["result"]["partitions"]] == [("main", True)]
    data = {k: v for k, v in res["result"]["entry"]["data"].items() if k in {f["key"] for f in res["result"]["settings_form"]}}
    res = await _ws(client, type="vigil_alarm/save_settings", data={**data, "partition_name": "Villa"})
    assert res["result"]["ok"] is True, res
    await hass.async_block_till_done()
    res = await _ws(client, type="vigil_alarm/get")
    assert res["result"]["partitions"][0]["name"] == "Villa"


async def test_saving_the_settings_keeps_the_first_partition(hass, hass_ws_client):
    from .test_panel import _ws
    entry, client = await _admin(hass, hass_ws_client)
    res = await _ws(client, type="vigil_alarm/get")
    keys = {f["key"] for f in res["result"]["settings_form"]}
    assert not keys & {"modes", "partition_name", "exit_delay_away", "default_entry_delay", "trigger_time", "chime_entity"}
    before = dict(entry.data)
    data = {k: v for k, v in res["result"]["entry"]["data"].items() if k in keys}  # what the settings tab sends
    res = await _ws(client, type="vigil_alarm/save_settings", data={**data, "abort_seconds": 45})
    assert res["result"]["ok"] is True, res
    await hass.async_block_till_done()
    assert entry.data["abort_seconds"] == 45
    for key in ("modes", "exit_delay_away", "default_entry_delay"):
        assert entry.data[key] == before[key]


async def test_found_sensors_can_be_added_to_a_partition(hass, hass_ws_client):
    from custom_components.vigil_alarm.items import items_of
    from .test_panel import _ws
    entry, client = await _admin(hass, hass_ws_client, GARAGE, GARAGE_GROUP)
    items = [{"name": "Shed", "entity_id": "binary_sensor.shed", "cls": "intrusion", "type": "instant",
              "sensor_groups": ["g_gar"], "at_arm_open": "bypass", "partition": "p_gar"}]
    res = await _ws(client, type="vigil_alarm/save_many", items=items)
    assert res["success"] and res["result"]["ok"] is True, res
    await hass.async_block_till_done()
    shed = [s for s in items_of(entry).values() if s.title == "Shed"][0]
    assert shed.data["partition"] == "p_gar"


async def test_default_groups_can_be_made_for_a_partition(hass, hass_ws_client):
    from custom_components.vigil_alarm.items import items_of
    from .test_panel import _ws
    entry, client = await _admin(hass, hass_ws_client, GARAGE)
    res = await _ws(client, type="vigil_alarm/create_default_groups", partition="p_gar")
    assert res["result"]["ok"] is True and len(res["result"]["ids"]) == 2, res
    await hass.async_block_till_done()
    made = [items_of(entry)[i] for i in res["result"]["ids"]]
    assert all(g.data["partition"] == "p_gar" and g.title.endswith("(Garage)") for g in made)
    assert all(set(g.data["modes"]) <= {"away"} for g in made)  # the garage has only Away
    again = await _ws(client, type="vigil_alarm/create_default_groups", partition="p_gar")
    assert again["result"]["ids"] == []
    res = await _ws(client, type="vigil_alarm/create_default_groups", partition="nope")
    assert res["result"]["errors"] == {"partition": "unknown_partition"}


# ---- the choice of a partition is always made, a panel has a default partition and can switch

async def _save(client, kind, **data):
    from .test_panel import _ws
    return (await _ws(client, type="vigil_alarm/save", kind=kind, data=data))["result"]


async def test_with_more_than_one_partition_the_choice_of_partitions_is_always_made(hass, hass_ws_client):
    entry, client = await _admin(hass, hass_ws_client, *EXTRA)
    await hass.async_block_till_done()
    # nothing chosen is an error for everything that has the choice
    assert (await _save(client, "user", name="Eva", code="2468", partitions=[]))["errors"] == {"partitions": "partitions_required"}
    assert (await _save(client, "user", name="Eva", code="2468"))["errors"] == {"partitions": "partitions_required"}
    assert (await _save(client, "notification", name="Phone", service="notify.phone", categories=["alarm"]))["errors"] == {
        "partitions": "partitions_required"}
    assert (await _save(client, "siren", name="Hall siren", control="siren.hall", causes=["intrusion"]))["errors"] == {
        "partitions": "partitions_required"}
    assert (await _save(client, "panel", name="Hall", device="esphome", panel_id="hall", partitions=[],
                        default_partition="main"))["errors"] == {"partitions": "partitions_required"}
    # a partition, or "all", is a choice
    assert (await _save(client, "user", name="Eva", code="2468", partitions=["p_gar"]))["ok"] is True
    assert (await _save(client, "user", name="Ben", code="1357", partitions=["all"]))["ok"] is True
    from custom_components.vigil_alarm.items import items_of
    users = {s.title: s.data for s in items_of(entry).values() if s.subentry_type == "user"}
    assert users["Eva"]["partitions"] == ["p_gar"]
    assert "partitions" not in users["Ben"]  # all of them is stored as nothing, so a later partition is included


async def test_with_one_partition_nothing_has_to_be_chosen(hass, hass_ws_client):
    from .test_panel import _ws
    entry = await _setup(hass, make_entry())
    client = await hass_ws_client(hass)
    assert (await _save(client, "user", name="Eva", code="2468"))["ok"] is True


async def test_a_panel_needs_a_default_partition_it_may_use(hass, hass_ws_client):
    entry, client = await _admin(hass, hass_ws_client, *EXTRA)
    await hass.async_block_till_done()
    base = {"name": "Hall", "device": "esphome", "panel_id": "hall"}
    assert (await _save(client, "panel", **base, partitions=["all"]))["errors"] == {"default_partition": "default_partition_required"}
    assert (await _save(client, "panel", **base, partitions=["main"], default_partition="p_gar"))["errors"] == {
        "default_partition": "default_partition_not_allowed"}
    assert (await _save(client, "panel", **base, partitions=["main"], default_partition="all"))["errors"] == {
        "default_partition": "default_partition_not_allowed"}  # "all" needs more than one partition
    res = await _save(client, "panel", **base, partitions=["all"], default_partition="all")
    assert res["ok"] is True, res
    from custom_components.vigil_alarm.items import items_of
    assert items_of(entry)[res["id"]].data["default_partition"] == "all"


async def test_a_panel_starts_on_its_default_partition_and_can_switch(hass):
    panel = sub("panel", "Hall", {"panel_id": "hall", "default_partition": "p_gar", "can_disarm": True,
                                  "can_bypass": True, "can_silence": True, "allowed_modes": []}, "pp")
    entry, home, garage, everything = await house(hass, panel)
    registry = entry.runtime_data.panels
    item = registry.get("hall")
    profile = registry.profile(item)
    assert profile["default_partition"] == profile["selected_partition"] == "p_gar"
    assert profile["alarm"] == [garage]  # a firmware from before this knows only that one
    assert profile["partition_total"] == 2 and profile["partition_return_seconds"] == 30
    assert profile["partition_list"].split("\n") == ["main|Home|disarmed", "p_gar|Garage|disarmed", "all||disarmed"]
    assert profile["view_state"] == "disarmed" and profile["view_mixed"] is False
    assert profile["allowed_modes"] == ["away"] and profile["modes_mask"] == 2
    # the garage is armed: the screen shows that
    await act(hass, garage, "alarm_arm_away", code="1234")
    profile = registry.profile(item)
    assert profile["view_state"] == "armed_away" and profile["view_mode"] == "away"
    assert "p_gar|Garage|armed_away" in profile["partition_list"].split("\n")
    # switch to the house, then to all
    await hass.services.async_call("vigil_alarm", "select_partition", {"source": "hall", "partition": "main"}, blocking=True)
    profile = registry.profile(item)
    assert profile["selected_partition"] == "main" and profile["view_state"] == "disarmed" and profile["allowed_modes"] == ["home", "away", "night"]
    await hass.services.async_call("vigil_alarm", "select_partition", {"source": "hall", "partition": "all"}, blocking=True)
    profile = registry.profile(item)
    assert profile["view_state"] == "armed_away" and profile["view_mixed"] is True  # the garage is armed, the house is not
    assert profile["partition_list"].split("\n")[-1] == "all||armed_away|mixed"
    assert profile["modes_mask"] == 7  # the modes that any of them has
    # back to the default
    await hass.services.async_call("vigil_alarm", "select_partition", {"source": "hall", "partition": "p_gar"}, blocking=True)
    assert registry.profile(item)["selected_partition"] == "p_gar"


async def test_a_panel_cannot_select_a_partition_it_may_not_use(hass):
    panel = sub("panel", "Hall", {"panel_id": "hall", "partitions": ["p_gar"], "default_partition": "p_gar",
                                  "can_disarm": True, "can_bypass": True, "can_silence": True, "allowed_modes": []}, "pp")
    entry, home, garage, everything = await house(hass, panel)
    for partition in ("main", "all", "nope"):
        with pytest.raises(ServiceValidationError):
            await hass.services.async_call("vigil_alarm", "select_partition", {"source": "hall", "partition": partition}, blocking=True)
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call("vigil_alarm", "select_partition", {"source": "nobody", "partition": "p_gar"}, blocking=True)
    profile = entry.runtime_data.panels.profile(entry.runtime_data.panels.get("hall"))
    assert [p["id"] for p in profile["partitions"]] == ["p_gar"] and "all||" not in profile["partition_list"]


async def test_arming_without_a_partition_from_a_panel_is_the_partition_of_that_panel(hass):
    # a firmware from before partitions never names one: it gets the partition the panel starts on
    panel = sub("panel", "Garage panel", {"panel_id": "garage-panel", "partitions": ["p_gar"], "default_partition": "p_gar",
                                          "can_disarm": True, "can_bypass": True, "can_silence": True, "allowed_modes": []}, "pp")
    entry, home, garage, everything = await house(hass, panel)
    await hass.services.async_call("vigil_alarm", "arm", {"mode": "away", "code": "1234", "source": "garage-panel"}, blocking=True)
    assert hass.states.get(garage).state == "armed_away" and hass.states.get(home).state == "disarmed"
    await hass.services.async_call("vigil_alarm", "disarm", {"code": "1234", "source": "garage-panel"}, blocking=True)
    assert hass.states.get(garage).state == "disarmed"


async def test_the_time_to_return_is_a_setting(hass, hass_ws_client):
    from .test_panel import _ws
    entry, client = await _admin(hass, hass_ws_client, *EXTRA)
    res = (await _ws(client, type="vigil_alarm/get"))["result"]
    assert res["entry"]["data"]["partition_return_seconds"] == 30
    assert "partition_return_seconds" in [f["key"] for f in res["settings_form"]]
    data = {**res["entry"]["data"], "partition_return_seconds": 5000}
    assert (await _ws(client, type="vigil_alarm/save_settings", data=data))["result"]["errors"] == {"partition_return_seconds": "seconds_range"}
    data["partition_return_seconds"] = 90
    assert (await _ws(client, type="vigil_alarm/save_settings", data=data))["result"]["ok"] is True
    await hass.async_block_till_done()
    assert entry.data["partition_return_seconds"] == 90


async def test_the_tamper_contact_of_a_sensor_watches_in_the_partition_of_that_sensor(hass):
    tamper = sub("zone", "Garage door (tamper)", {"entity_id": "binary_sensor.garage_tamper", "cls": "tamper",
                 "companion_of": "gdoor"}, "gtamper")
    hass.states.async_set("binary_sensor.garage_tamper", "off")
    entry, home, garage, everything = await house(hass, tamper)
    manager = entry.runtime_data
    assert "gtamper" in manager.partitions["p_gar"].config.sensors
    assert "gtamper" not in manager.partitions[next(iter(manager.partitions))].config.sensors
    # on the panel list of a panel that may use both: the contact has the partition of its sensor
    rows = [r.split("|") for r in manager.panel_rows(list(manager.partitions)).split("\n")]
    row = next(r for r in rows if r[1] == "binary_sensor.garage_tamper")
    assert row[4] == "p_gar"
    # the profile of a panel that only has the house does not list it at all
    assert "binary_sensor.garage_tamper" not in manager.snapshot(next(iter(manager.partitions)))["panel_sensors"]


async def test_a_tamper_sensor_can_be_given_a_partition_or_all(hass):
    from custom_components.vigil_alarm.editing import EditError, partition_names
    from custom_components.vigil_alarm.editing import _sensor as edit_sensor
    alone = sub("zone", "Loose tamper", {"entity_id": "binary_sensor.loose_tamper", "cls": "tamper", "partition": "p_gar"}, "ltamper")
    hass.states.async_set("binary_sensor.loose_tamper", "off")
    entry, home, garage, everything = await house(hass, alone)
    manager = entry.runtime_data
    first = next(iter(manager.partitions))
    assert "ltamper" in manager.partitions["p_gar"].config.sensors and "ltamper" not in manager.partitions[first].config.sensors
    # the form: "all" is stored as nothing, a known partition as itself, an unknown one is refused
    raw = {"entity_id": "binary_sensor.x_tamper", "cls": "tamper"}
    assert "partition" not in edit_sensor(entry, None, "X", {**raw, "tamper_partition": "all"})
    assert edit_sensor(entry, None, "X", {**raw, "tamper_partition": "p_gar"})["partition"] == "p_gar"
    with pytest.raises(EditError):
        edit_sensor(entry, None, "X", {**raw, "tamper_partition": "nope"})


async def test_the_last_alarm_says_in_which_partition_it_was(hass):
    """0.6.2: with more than one partition the alarm memory names the partition, also in the line for the panel."""
    entry, home, garage, everything = await house(hass)
    manager = entry.runtime_data
    await act(hass, garage, "alarm_arm_away", code="1234")
    hass.states.async_set("binary_sensor.garage_door", "on")
    await hass.async_block_till_done()
    assert manager.alarmmemory.view()["partition_name"] == "Garage"
    assert hass.states.get(home).attributes["last_alarm"]["partition"] == "Garage"


async def test_the_last_alarm_names_no_partition_with_one_partition(hass, freezer):
    from .test_alarm_features import _alarm_in_the_house

    entry, manager = await _alarm_in_the_house(hass, freezer)
    assert manager.alarmmemory.view()["partition_name"] is None
    assert hass.states.get("alarm_control_panel.vigil_alarm").attributes["last_alarm"]["partition"] is None
