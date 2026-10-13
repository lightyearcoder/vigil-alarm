"""Config validation, serialisation and engine API checks."""

from __future__ import annotations

import copy
import json
import pathlib

import pytest
import yaml

from vigil_core import Config, ConfigError, Engine

HOUSE = yaml.safe_load((pathlib.Path(__file__).parent / "configs.yaml").read_text())["house"]


def _with(**patch):
    data = copy.deepcopy(HOUSE)
    for key, value in patch.items():
        data[key] = value
    return data


def test_config_round_trips_and_is_json_serialisable():
    config = Config.from_dict(HOUSE)
    exported = config.to_dict()
    json.dumps(exported)  # must not raise
    assert Config.from_dict(exported).to_dict() == exported
    assert exported["version"] == 1


def _sensor(**fields):
    return {"sensors": {"z": fields}, "rules": {}}  # rules cleared: they refer to house sensors


@pytest.mark.parametrize(
    "patch,fragment",
    [
        ({"modes": {}}, "at least one mode is required"),
        ({"version": 99}, "unsupported config version"),
        ({"trigger_time": 0}, "trigger_time must be > 0"),
        ({"default_entry_delay": -1}, "default_entry_delay must be >= 0"),
        (_sensor(cls="nope"), "unknown class"),
        (_sensor(cls="intrusion", modes=["away"], type="nope"), "unknown type"),
        (_sensor(cls="intrusion", modes=[]), "needs at least one mode"),
        (_sensor(cls="intrusion", modes=["unknown"]), "unknown mode"),
        (_sensor(cls="intrusion", modes=["away"], at_arm_open="x"), "unknown at_arm_open"),
        (_sensor(cls="intrusion", modes=["away"], on_unavailable="x"), "unknown on_unavailable"),
        (_sensor(cls="intrusion", modes=["away"], gas_type="co"), "only valid for class gas"),
        (_sensor(cls="gas", gas_type="helium"), "unknown gas_type"),
        (_sensor(cls="intrusion", modes=["away"], entry_delay=-5), "entry_delay must be >= 0"),
        (_sensor(cls="intrusion", modes=["away"], entry_delay={"x": 1}), "unknown mode"),
        (_sensor(cls="fire", on_unavailable="bypass"), "cannot be bypassed"),
        (_sensor(cls="gas", on_unavailable="bypass"), "cannot be bypassed"),
    ],
)
def test_invalid_sensor_and_mode_config_is_rejected(patch, fragment):
    with pytest.raises(ConfigError, match=fragment):
        Config.from_dict(_with(**patch))


@pytest.mark.parametrize(
    "rules,fragment",
    [
        ({"g": {"sensors": ["living_pir", "smoke_hall"]}}, "intrusion-only"),
        ({"g": {"sensors": ["living_pir", "front_door"]}}, "must be of type instant"),
        ({"g": {"sensors": ["living_pir", "nope"]}}, "unknown sensor"),
        ({"g": {"sensors": ["living_pir", "kitchen_pir"], "required": 3}}, "required must be between"),
        ({"g": {"sensors": ["living_pir", "kitchen_pir"], "required": 1}}, "required must be between"),
        ({"g": {"sensors": ["living_pir", "kitchen_pir"], "window": 0}}, "window must be > 0"),
        (
            {
                "g1": {"sensors": ["living_pir", "kitchen_pir"]},
                "g2": {"sensors": ["kitchen_pir", "bedroom_pir"]},
            },
            "more than one rule",
        ),
    ],
)
def test_invalid_rules_are_rejected(rules, fragment):
    with pytest.raises(ConfigError, match=fragment):
        Config.from_dict(_with(rules=rules))


def test_gas_sensor_defaults_to_other():
    data = _with(sensors={"g": {"cls": "gas"}}, rules={})
    assert Config.from_dict(data).sensors["g"].gas_type == "other"


def test_time_cannot_go_backwards():
    engine = Engine(Config.from_dict(HOUSE))
    engine.advance(10)
    with pytest.raises(ValueError):
        engine.advance(5)


def test_unknown_mode_sensor_and_value_are_programming_errors():
    engine = Engine(Config.from_dict(HOUSE))
    with pytest.raises(ValueError):
        engine.arm("vacation")
    with pytest.raises(ValueError):
        engine.set_sensor("nope", "open")
    with pytest.raises(ValueError):
        engine.set_sensor("front_door", "ajar")


def test_timer_due_at_the_same_time_fires_before_the_input():
    """Entry delay ends at t=130; a disarm at t=130 is too late."""
    engine = Engine(Config.from_dict(HOUSE))
    engine.arm("away")
    engine.advance(60)
    engine.advance(100)
    engine.set_sensor("front_door", "open")
    engine.advance(130)
    engine.disarm("anna")
    types = [e["type"] for e in engine.events]
    assert types.index("triggered") < types.index("disarmed")


def test_on_event_callback_receives_every_event():
    seen = []
    engine = Engine(Config.from_dict(HOUSE), on_event=seen.append)
    engine.arm("home", user="anna")
    assert seen == engine.events and seen[0]["type"] == "armed"


@pytest.mark.parametrize(
    "sensor,expected",
    [
        ("front_door", "block"),
        ("living_pir", "block"),
        ("tamper_siren", "block"),
        ("smoke_hall", "notify"),  # a broken smoke detector must not block arming
        ("gas_kitchen", "notify"),
        ("co_living", "notify"),
        ("water_kitchen", "notify"),
        ("cellar_window", "trigger"),  # explicit setting wins over the class default
    ],
)
def test_default_on_unavailable_per_class(sensor, expected):
    assert Config.from_dict(HOUSE).sensors[sensor].on_unavailable == expected


def test_bypass_policy_is_allowed_for_intrusion_and_tamper_sensors():
    data = _with(
        sensors={
            "a": {"cls": "intrusion", "modes": ["away"], "on_unavailable": "bypass"},
            "t": {"cls": "tamper", "on_unavailable": "bypass"},
        },
        rules={},
    )
    config = Config.from_dict(data)
    assert config.sensors["a"].on_unavailable == config.sensors["t"].on_unavailable == "bypass"
    assert Config.from_dict(config.to_dict()).to_dict() == config.to_dict()


def test_water_sensor_is_valid_and_cannot_be_in_a_confirmation_rule():
    data = _with(sensors={"w": {"cls": "water"}, "a": {"cls": "intrusion", "modes": ["away"]}}, rules={})
    config = Config.from_dict(data)
    assert config.sensors["w"].always_on and not config.sensors["w"].blocks_arming_when_open
    assert Config.from_dict(config.to_dict()).to_dict() == config.to_dict()
    data["rules"] = {"g": {"sensors": ["a", "w"]}}
    with pytest.raises(ConfigError, match="intrusion-only"):
        Config.from_dict(data)
    with pytest.raises(ConfigError, match="only valid for class gas"):
        Config.from_dict(_with(sensors={"w": {"cls": "water", "gas_type": "co"}}, rules={}))


def test_snapshot_exposes_technical_alarms():
    engine = Engine(Config.from_dict(HOUSE))
    engine.set_sensor("water_bath", "open")
    assert engine.snapshot()["technical_alarms"] == ["water_bath"]
    assert engine.state == "disarmed"


# ------------------------------------------------------------ persistence


def _armed_and_pending():
    engine = Engine(Config.from_dict(HOUSE))
    engine.arm("away", user="anna")
    engine.advance(60)
    engine.advance(100)
    engine.set_sensor("front_door", "open")  # entry delay 30 -> due 130
    return engine


def test_next_due_reports_the_earliest_timer():
    engine = Engine(Config.from_dict(HOUSE))
    assert engine.next_due() is None
    engine.arm("away")
    assert engine.next_due() == 60
    engine.advance(60)
    assert engine.next_due() is None


def test_timer_that_expired_during_downtime_fires_with_its_original_time():
    engine = _armed_and_pending()
    state = json.loads(json.dumps(engine.export_state()))
    fresh = Engine(Config.from_dict(HOUSE))
    fresh.restore_state(state)
    assert fresh.state == "pending" and fresh.now == 100
    fresh.advance(200)  # HA was down until t=200
    assert fresh.state == "triggered"
    assert fresh.events[-1]["type"] == "triggered" and fresh.events[-1]["t"] == 130


def test_restore_rejects_bad_state_and_leaves_the_engine_untouched():
    good = _armed_and_pending().export_state()
    bad_cases = [
        {**good, "version": 99},
        {**good, "mode": "vacation"},
        {**good, "state": "exploded"},
        {**good, "timers": [[1, 1, "bogus", None]]},
        {**good, "sensors": {"front_door": {**good["sensors"]["front_door"], "value": "ajar"}}},
        {k: v for k, v in good.items() if k != "state"},
    ]
    for bad in bad_cases:
        engine = Engine(Config.from_dict(HOUSE))
        with pytest.raises(ValueError):
            engine.restore_state(bad)
        assert engine.state == "disarmed" and engine.next_due() is None


def test_restore_copes_with_a_changed_config():
    state = _armed_and_pending().export_state()
    data = copy.deepcopy(HOUSE)
    del data["sensors"]["front_door"]
    del data["rules"]
    data["sensors"]["new_sensor"] = {"cls": "intrusion", "modes": ["away"]}
    engine = Engine(Config.from_dict(data))
    engine.restore_state(state)
    assert engine.sensor_status("new_sensor") == "closed"
    engine.advance(200)  # pending sensor is gone: the timer must not crash
    assert engine.state in ("armed_away", "pending", "triggered")


def test_is_bypassed_reports_manual_bypass_only():
    engine = Engine(Config.from_dict(HOUSE))
    assert not engine.is_bypassed("window_living")
    engine.bypass("window_living")
    assert engine.is_bypassed("window_living")
    engine.unbypass("window_living")
    assert not engine.is_bypassed("window_living")
    with pytest.raises(ValueError):
        engine.is_bypassed("nope")


def test_a_state_saved_with_the_old_names_still_restores():
    """Before sensors and rules got their names, states used "zones" and "groups"."""
    engine = _armed_and_pending()
    current = json.loads(json.dumps(engine.export_state()))
    legacy = {k: v for k, v in current.items() if k not in ("sensors", "rules", "cause_sensor", "pending_sensor")}
    legacy["zones"] = current["sensors"]
    legacy["groups"] = current["rules"]
    legacy["cause_zone"] = current["cause_sensor"]
    legacy["pending_zone"] = current["pending_sensor"]
    legacy["timers"] = [[d, s, "group" if k == "rule" else k, key] for d, s, k, key in current["timers"]]
    fresh = Engine(Config.from_dict(HOUSE))
    fresh.restore_state(legacy)
    assert fresh.state == "pending" and fresh._pending_sensor == engine._pending_sensor
    fresh.advance(200)
    assert fresh.state == "triggered"
    # a rule timer in the old format is carried over under its new kind
    with_rule = {**legacy, "timers": [[150.0, 99, "group", "downstairs"]], "groups": {"downstairs": ["living_pir"]}}
    fresh = Engine(Config.from_dict(HOUSE))
    fresh.restore_state(with_rule)
    assert fresh.next_due() == 150.0
