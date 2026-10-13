"""Runs the data-driven scenarios in tests/scenarios/*.yaml against the engine.

Scenario format (see README):

    - name: ...
      config: house              # key in configs.yaml or in the file's own `configs:`
      steps:
        - {t: 0, arm: away, user: anna}
        - {t: 5, sensor: front_door, value: open}
        - {t: 9, expect: {state: pending}}
      events: [{t: 0, type: arming_started, ...}]   # complete, ordered list
      events_ignore: [sensor_faulted]                  # event types left out of the comparison

Event dicts are compared as subsets (only the listed keys are checked), but the
number and order of events must match exactly.
"""

from __future__ import annotations

import json
import pathlib
from typing import Any

import pytest
import yaml

from vigil_core import Config, Engine

HERE = pathlib.Path(__file__).parent


def _load_cases() -> list[Any]:
    shared = yaml.safe_load((HERE / "configs.yaml").read_text())
    cases = []
    for path in sorted((HERE / "scenarios").glob("*.yaml")):
        doc = yaml.safe_load(path.read_text())
        configs = {**shared, **(doc.get("configs") or {})}
        for scenario in doc["scenarios"]:
            cases.append(
                pytest.param(scenario, configs, id=f"{path.stem}::{scenario['name']}")
            )
    return cases


def _check_expect(engine: Engine, expect: dict[str, Any], where: str) -> None:
    snap = engine.snapshot()
    for key, want in expect.items():
        if key == "sensor_status":
            for sensor, status in want.items():
                got = engine.sensor_status(sensor)
                assert got == status, f"{where}: sensor_status[{sensor}] = {got!r}, want {status!r}"
            continue
        assert key in snap, f"{where}: unknown snapshot key {key!r}"
        assert snap[key] == want, f"{where}: {key} = {snap[key]!r}, want {want!r}"


def _restart(engine: Engine, config: Config) -> Engine:
    """Simulate an HA restart: export, JSON round trip, new engine, restore."""
    state = json.loads(json.dumps(engine.export_state()))
    fresh = Engine(config)
    fresh.restore_state(state)
    fresh.events = list(engine.events)
    return fresh


def _format(events: list[dict[str, Any]]) -> str:
    return "\n".join(f"  {e}" for e in events) or "  (none)"


def _run(scenario: dict[str, Any], configs: dict[str, Any], restart: bool) -> None:
    config = Config.from_dict(configs[scenario["config"]])
    engine = Engine(config)

    for i, step in enumerate(scenario["steps"]):
        where = f"step {i} (t={step['t']})"
        engine.advance(step["t"])
        if "arm" in step:
            engine.arm(step["arm"], user=step.get("user"))
        elif "disarm" in step:
            engine.disarm(user=step["disarm"])
        elif "sensor" in step:
            engine.set_sensor(step["sensor"], step["value"])
        elif "bypass" in step:
            engine.bypass(step["bypass"], user=step.get("user"))
        elif "unbypass" in step:
            engine.unbypass(step["unbypass"], user=step.get("user"))
        if restart:
            engine = _restart(engine, config)
        if "expect" in step:
            _check_expect(engine, step["expect"], where)

    ignore = set(scenario.get("events_ignore", []))
    actual = [e for e in engine.events if e["type"] not in ignore]
    expected = scenario.get("events", [])
    assert len(actual) == len(expected), (
        f"event count {len(actual)} != {len(expected)}\n"
        f"actual:\n{_format(actual)}\nexpected:\n{_format(expected)}"
    )
    for i, (got, want) in enumerate(zip(actual, expected)):
        for key, value in want.items():
            assert got.get(key) == value, (
                f"event {i}: {key} = {got.get(key)!r}, want {value!r}\n"
                f"actual:\n{_format(actual)}\nexpected:\n{_format(expected)}"
            )


@pytest.mark.parametrize("scenario,configs", _load_cases())
def test_scenario(scenario: dict[str, Any], configs: dict[str, Any]) -> None:
    _run(scenario, configs, restart=False)


@pytest.mark.parametrize("scenario,configs", _load_cases())
def test_scenario_survives_a_restart_after_every_step(
    scenario: dict[str, Any], configs: dict[str, Any]
) -> None:
    """Same expectations when the engine is restarted from persisted state after each step."""
    _run(scenario, configs, restart=True)
