from __future__ import annotations

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.vigil.const import DOMAIN
from custom_components.vigil.items import items_of
from custom_components.vigil.manager import build_config

from .common import sub


def _v1_entry() -> MockConfigEntry:
    """An installation from before sensor groups: the modes are stored on each sensor."""
    base = {"entity_id": "binary_sensor.x", "cls": "intrusion", "at_arm_open": "wait_clear", "type": "instant"}
    return MockConfigEntry(
        domain=DOMAIN, title="Vigil Alarm", unique_id=DOMAIN, version=1,
        data={"modes": ["home", "away", "night"], "exit_delay_home": 0, "exit_delay_away": 60,
              "exit_delay_night": 10, "default_entry_delay": 30, "trigger_time": 0, "code_arm_required": True},
        subentries_data=[
            sub("zone", "Door", {**base, "entity_id": "binary_sensor.door", "type": "delayed",
                                 "modes": ["home", "away", "night"]}, "door"),
            sub("zone", "Window", {**base, "entity_id": "binary_sensor.window", "modes": ["home", "away", "night"]}, "window"),
            sub("zone", "Living PIR", {**base, "entity_id": "binary_sensor.pir", "modes": ["away"]}, "pir"),
            sub("zone", "Hall PIR", {**base, "entity_id": "binary_sensor.hall", "modes": ["night", "away"]}, "hall"),
            sub("zone", "Smoke", {"entity_id": "binary_sensor.smoke", "cls": "fire"}, "smoke"),
            sub("group", "Downstairs", {"zones": ["pir", "hall"], "required": 2, "window": 60, "escalate": True}, "rule1"),
        ],
    )


async def test_modes_on_sensors_become_sensor_groups_without_changing_behaviour(hass):
    entry = _v1_entry()
    entry.add_to_hass(hass)
    for name in ("door", "window", "pir", "hall", "smoke"):
        hass.states.async_set(f"binary_sensor.{name}", "off")
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.version == 3 and not entry.subentries
    groups = {s.subentry_id: s for s in items_of(entry).values() if s.subentry_type == "sensor_group"}
    # one group per distinct set of modes: all three, away only, away + night
    assert sorted(g.title for g in groups.values()) == ["Away", "Away + Night", "Home + Away + Night"]
    sensors = {s.title: s for s in items_of(entry).values() if s.subentry_type == "zone"}
    assert all("modes" not in s.data for s in sensors.values())
    assert sensors["Door"].data["sensor_groups"] == sensors["Window"].data["sensor_groups"]  # same set, same group
    assert sensors["Door"].data["sensor_groups"] != sensors["Living PIR"].data["sensor_groups"]
    assert "sensor_groups" not in sensors["Smoke"].data  # life safety is always on
    rule = items_of(entry)["rule1"].data  # confirmation rules stored their sensors as "zones"
    assert "zones" not in rule and rule["sensors"] == ["pir", "hall"] and rule["escalate"] is True
    config = build_config(entry)
    assert list(config.rules["rule1"].sensors) == ["pir", "hall"]
    assert list(config.sensors["door"].modes) == ["home", "away", "night"]
    assert list(config.sensors["pir"].modes) == ["away"]
    assert list(config.sensors["hall"].modes) == ["away", "night"]
    # the integration runs normally afterwards
    assert hass.states.get("alarm_control_panel.vigil_alarm").state == "disarmed"


async def test_migration_runs_once(hass):
    entry = _v1_entry()
    entry.add_to_hass(hass)
    for name in ("door", "window", "pir", "hall", "smoke"):
        hass.states.async_set(f"binary_sensor.{name}", "off")
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    count = len(items_of(entry))
    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    assert len(items_of(entry)) == count and entry.version == 3


async def test_an_entry_from_a_newer_version_is_left_alone(hass):
    entry = MockConfigEntry(domain=DOMAIN, title="Vigil Alarm", unique_id=DOMAIN, version=99, data={"modes": ["away"]})
    entry.add_to_hass(hass)
    assert not await hass.config_entries.async_setup(entry.entry_id)
    assert entry.version == 99


async def test_items_leave_the_subentries_but_entities_and_devices_stay(hass):
    """Version 2 kept the items as subentries; they move to the options and keep their entities."""
    from homeassistant.helpers import device_registry as dr, entity_registry as er

    entry = MockConfigEntry(
        domain=DOMAIN, title="Vigil Alarm", unique_id=DOMAIN, version=2,
        data={"modes": ["home", "away"], "exit_delay_home": 0, "exit_delay_away": 60, "default_entry_delay": 30,
              "trigger_time": 0, "code_arm_required": True},
        subentries_data=[
            sub("zone", "Door", {"entity_id": "binary_sensor.door", "cls": "intrusion", "type": "delayed",
                                 "sensor_groups": ["g1"]}, "door"),
            sub("sensor_group", "All", {"modes": ["home", "away"]}, "g1"),
        ],
    )
    entry.add_to_hass(hass)
    ent_reg, dev_reg = er.async_get(hass), dr.async_get(hass)
    dev = dev_reg.async_get_or_create(
        config_entry_id=entry.entry_id, config_subentry_id="door", identifiers={(DOMAIN, f"{entry.entry_id}_door")}, name="Door"
    )
    ent = ent_reg.async_get_or_create(
        "sensor", DOMAIN, f"{entry.entry_id}_door_status", config_entry=entry, config_subentry_id="door",
        device_id=dev.id, suggested_object_id="door_status",
    )
    hass.states.async_set("binary_sensor.door", "off")
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.version == 3 and not entry.subentries
    assert set(items_of(entry)) == {"door", "g1"}
    kept = ent_reg.async_get(ent.entity_id)
    assert kept is not None and kept.config_subentry_id is None
    assert dev_reg.async_get(dev.id) is not None
    assert hass.states.get("sensor.door_status").state == "closed"
