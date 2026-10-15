"""The example dashboard: valid, pointing at entities that exist, and its templates render."""

from __future__ import annotations

import pathlib

import pytest
import re

import yaml
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.template import Template

from .common import PANEL, make_entry
from .test_integration import _call, _setup

EXAMPLES = pathlib.Path(__file__).parents[2] / "examples"


def _cards():
    data = yaml.safe_load((EXAMPLES / "dashboard.yaml").read_text())
    return data["views"][0]["cards"]


def _walk(node):
    if isinstance(node, dict):
        yield node
        for v in node.values():
            yield from _walk(v)
    elif isinstance(node, list):
        for v in node:
            yield from _walk(v)


@pytest.mark.parametrize("language", ["en", "nl"])
async def test_the_dashboard_only_uses_entities_the_integration_creates(hass, language):
    hass.config.language = language  # entity ids must not depend on it
    await _setup(hass)
    known = set(hass.states.async_entity_ids()) | {e for e in er.async_get(hass).entities}
    wanted = set()
    for node in _walk(_cards()):
        if isinstance(node.get("entity"), str):
            wanted.add(node["entity"])
        if isinstance(node.get("entity_id"), str):
            wanted.add(node["entity_id"])
    assert PANEL in wanted and "event.vigil_alarm_alarm_events" in wanted
    assert wanted - known == set(), wanted - known
    # the services it calls exist
    text = (EXAMPLES / "dashboard.yaml").read_text()
    for service in re.findall(r"perform_action: (\w+)\.(\w+)", text):
        assert hass.services.has_service(*service), service


async def test_the_dashboard_templates_render(hass):
    await _setup(hass)
    templates = [n["content"] for n in _walk(_cards()) if n.get("type") == "markdown"]
    templates += [c["value_template"] for n in _walk(_cards()) if n.get("type") == "conditional"
                  for c in n["conditions"]]
    assert len(templates) == 3
    status, attention, condition = (Template(t, hass) for t in (templates[0], templates[1], templates[2]))
    assert "Disarmed" in status.async_render()
    assert condition.async_render() is False

    await _call(hass, "alarm_arm_away", code="1234")
    hass.states.async_set("binary_sensor.living_pir", "unavailable")
    hass.states.async_set("binary_sensor.smoke", "on")
    await hass.async_block_till_done()
    text = status.async_render()
    assert "Triggered" in text and "fire" in text and "Smoke" in text
    assert condition.async_render() is True
    assert "Living PIR" in attention.async_render()
