"""The texts a person can see: every error code the code can raise must have text, in both languages."""

from __future__ import annotations

import json
import pathlib
import re

ROOT = pathlib.Path(__file__).parents[2] / "custom_components" / "vigil"


def _keys(node, prefix=""):
    if isinstance(node, dict):
        for k, v in node.items():
            yield from _keys(v, f"{prefix}.{k}" if prefix else k)
    else:
        yield prefix


def test_both_languages_have_the_same_keys():
    en = set(_keys(json.loads((ROOT / "translations/en.json").read_text())))
    nl = set(_keys(json.loads((ROOT / "translations/nl.json").read_text())))
    assert en == nl, sorted(en ^ nl)


def _panel_only_codes() -> set[str]:
    """Codes only the panel sends (not raised by the shared editing code)."""
    codes: set[str] = set()
    for line in (ROOT / "panel.py").read_text().splitlines():
        if "EditError(" in line:
            codes |= set(re.findall(r'(?::|=)\s*"([a-z_]+)"', line))
    return codes - {"invalid_config"}


def _codes_in_editing() -> set[str]:
    codes: set[str] = set()
    for line in (ROOT / "editing.py").read_text().splitlines():
        if "EditError(" in line or re.search(r'errors\[[^]]+\]\s*=', line):
            codes |= set(re.findall(r'(?::|=)\s*"([a-z_]+)"', line))
    return codes - {"invalid_config", "unknown_kind"}  # the last cannot happen: the panel only sends known kinds


def test_every_error_code_in_editing_has_a_text_in_the_panel():
    codes = _codes_in_editing()
    assert {"no_sensor_group", "unknown_sensor_group", "no_modes", "name_in_use", "no_credential",
            "service_not_found", "sensor_not_instant"} <= codes, codes
    js = (ROOT / "frontend/vigil-panel.js").read_text()
    missing = {c for c in codes if f"{c}:" not in js}
    assert not missing, f"the panel has no text for {missing}"
    panel_codes = _panel_only_codes()
    assert {"sensor_in_rule", "sensor_group_in_use"} <= panel_codes, panel_codes
    missing = {c for c in panel_codes if f"{c}:" not in js}
    assert not missing, f"the panel has no text for {missing}"


def test_the_entry_flow_has_its_texts():
    for lang in ("en", "nl"):
        data = json.loads((ROOT / f"translations/{lang}.json").read_text())
        assert {"no_modes", "invalid_config"} <= set(data["config"]["error"]), lang


def test_the_panel_shows_armed_home_away_and_night_as_armed():
    """The alarm reports armed_home, armed_away and armed_night; the panel has one text, "armed", plus the mode."""
    js = (ROOT / "frontend/vigil-panel.js").read_text()
    assert 'startsWith("armed_")' in js and js.count("this._stateText(live)") == 2


def test_every_event_type_cause_and_refusal_has_a_text_in_both_languages():
    """What Home Assistant shows for the event entity, the last-event sensor and the alarm attributes."""
    from custom_components.vigil.const import EVENT_TYPES

    for lang in ("en", "nl"):
        ent = json.loads((ROOT / f"translations/{lang}.json").read_text())["entity"]
        shown = ent["event"]["alarm_events"]["state_attributes"]["event_type"]["state"]
        assert set(shown) == set(EVENT_TYPES), (lang, set(shown) ^ set(EVENT_TYPES))
        assert ent["sensor"]["last_event"]["state"] == shown
        attrs = ent["alarm_control_panel"]["alarm"]["state_attributes"]
        assert {"intrusion", "fire", "gas", "tamper", "fault"} == set(attrs["cause"]["state"]), lang
        assert {"not_disarmed", "alarm_condition", "sensor_unavailable", "sensor_open"} == set(attrs["refuse_reason"]["state"])
        assert all(v and v != k for k, v in shown.items()), lang  # no raw key left as text
