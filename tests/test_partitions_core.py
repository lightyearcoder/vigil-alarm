"""Partitions in the pure core: splitting the config and the combined state."""

import pytest

from custom_components.vigil_alarm.vigil_core import ConfigError, aggregate, split_config

RAW = {
    "modes": {"home": {"exit_delay": 0}, "away": {"exit_delay": 30}},
    "sensors": {
        "door": {"cls": "intrusion", "modes": ["away"]},
        "garage": {"cls": "intrusion", "modes": ["away", "home"]},
        "pir1": {"cls": "intrusion", "modes": ["away"]},
        "pir2": {"cls": "intrusion", "modes": ["away"]},
        "smoke": {"cls": "fire"},
        "water": {"cls": "water"},
    },
    "rules": {"r": {"sensors": ["pir1", "pir2"]}},
}
OF = {"door": "house", "garage": "garage", "pir1": "house", "pir2": "house"}


def test_split_gives_every_partition_its_sensors_and_all_safety_sensors():
    cfgs = split_config(RAW, OF, ["house", "garage"])
    assert set(cfgs["house"].sensors) == {"door", "pir1", "pir2", "smoke", "water"}
    assert set(cfgs["garage"].sensors) == {"garage", "smoke", "water"}
    assert "r" in cfgs["house"].rules and not cfgs["garage"].rules


def test_sensor_without_partition_goes_to_the_first():
    cfgs = split_config(RAW, {}, ["house", "garage"])
    assert "garage" in cfgs["house"].sensors and "door" not in cfgs["garage"].sensors


def test_override_per_partition():
    raw = dict(RAW, partitions={"garage": {"modes": {"away": {"exit_delay": 5}}, "default_entry_delay": 10}})
    cfgs = split_config(raw, OF, ["house", "garage"])
    assert cfgs["garage"].modes["away"].exit_delay == 5 and cfgs["garage"].default_entry_delay == 10
    assert cfgs["house"].modes["away"].exit_delay == 30


def test_rule_across_partitions_is_refused():
    of = dict(OF, pir2="garage")
    with pytest.raises(ConfigError):
        split_config(RAW, of, ["house", "garage"])


def test_aggregate():
    assert aggregate({"a": "disarmed", "b": "disarmed"}).state == "disarmed"
    c = aggregate({"a": "armed_away", "b": "armed_away"})
    assert c.state == "armed_away" and not c.mixed and c.ha_state == "armed_away"
    c = aggregate({"a": "armed_away", "b": "disarmed"})
    assert c.state == "mixed" and c.mixed and c.ha_state == "armed_away"
    assert aggregate({"a": "armed_home", "b": "triggered", "c": "pending"}).ha_state == "triggered"
    assert aggregate({"a": "arming", "b": "armed_away"}).ha_state == "arming"
    assert aggregate({}).state == "disarmed"
