"""The texts a person can see: every error code the code can raise must have text, in every language."""

from __future__ import annotations

import json
import pathlib
import re
import string

from custom_components.vigil_alarm.languages import LANGUAGES

ROOT = pathlib.Path(__file__).parents[2] / "custom_components" / "vigil_alarm"


def _keys(node, prefix=""):
    if isinstance(node, dict):
        for k, v in node.items():
            yield from _keys(v, f"{prefix}.{k}" if prefix else k)
    else:
        yield prefix


def _leaves(node, prefix=""):
    if isinstance(node, dict):
        for k, v in node.items():
            yield from _leaves(v, f"{prefix}.{k}" if prefix else k)
    else:
        yield prefix, node


def _placeholders(text: str) -> list[str]:
    return sorted(name for _, name, _, _ in string.Formatter().parse(text) if name)


def test_every_language_has_the_same_keys():
    en = set(_keys(json.loads((ROOT / "translations/en.json").read_text(encoding="utf-8"))))
    for lang in LANGUAGES:
        other = set(_keys(json.loads((ROOT / f"translations/{lang}.json").read_text(encoding="utf-8"))))
        assert en == other, (lang, sorted(en ^ other))


def test_every_translation_has_the_same_placeholders_and_is_not_empty():
    en = dict(_leaves(json.loads((ROOT / "translations/en.json").read_text(encoding="utf-8"))))
    for lang in LANGUAGES:
        other = dict(_leaves(json.loads((ROOT / f"translations/{lang}.json").read_text(encoding="utf-8"))))
        for key, text in en.items():
            assert other[key].strip(), (lang, key)
            assert _placeholders(other[key]) == _placeholders(text), (lang, key)


def test_every_message_language_has_the_same_keys_and_placeholders():
    from custom_components.vigil_alarm.messages import MESSAGES, MODE_NAMES

    assert set(MESSAGES) == set(MODE_NAMES) == set(LANGUAGES)
    for lang, messages in MESSAGES.items():
        assert set(messages) == set(MESSAGES["en"]), (lang, set(messages) ^ set(MESSAGES["en"]))
        for key, text in messages.items():
            assert _placeholders(text) == _placeholders(MESSAGES["en"][key]), (lang, key)
        assert set(MODE_NAMES[lang]) == set(MODE_NAMES["en"]), lang


def test_language_of_maps_any_locale_to_a_supported_language():
    from custom_components.vigil_alarm.languages import language_of

    assert [language_of(x) for x in ("nl", "nl-NL", "de_AT", "FR", "it-CH", "es-419", "pt", "", None)] == [
        "nl", "nl", "de", "fr", "it", "es", "en", "en", "en",
    ]


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


def _panel_source() -> str:
    """The panel script and its texts (one file per language), as one string."""
    frontend = ROOT / "frontend"
    return "\n".join(p.read_text(encoding="utf-8") for p in [frontend / "vigil-panel.js", *sorted((frontend / "texts").glob("*.js"))])


def test_every_error_code_in_editing_has_a_text_in_the_panel():
    codes = _codes_in_editing()
    assert {"no_sensor_group", "unknown_sensor_group", "no_modes", "name_in_use", "no_credential",
            "service_not_found", "sensor_not_instant"} <= codes, codes
    js = _panel_source()
    missing = {c for c in codes if f"{c}:" not in js and f'"{c}":' not in js}
    assert not missing, f"the panel has no text for {missing}"
    panel_codes = _panel_only_codes()
    assert {"sensor_in_rule", "sensor_group_in_use"} <= panel_codes, panel_codes
    missing = {c for c in panel_codes if f"{c}:" not in js and f'"{c}":' not in js}
    assert not missing, f"the panel has no text for {missing}"


def test_the_entry_flow_has_its_texts():
    for lang in LANGUAGES:
        data = json.loads((ROOT / f"translations/{lang}.json").read_text(encoding="utf-8"))
        assert {"no_modes", "invalid_config"} <= set(data["config"]["error"]), lang


def test_the_panel_shows_armed_home_away_and_night_as_armed():
    """The alarm reports armed_home, armed_away and armed_night; the panel has one text, "armed", plus the mode."""
    js = (ROOT / "frontend/vigil-panel.js").read_text()
    assert 'startsWith("armed_")' in js and js.count("this._stateText(live)") == 2


def test_every_event_type_cause_and_refusal_has_a_text_in_every_language():
    """What Home Assistant shows for the event entity, the last-event sensor and the alarm attributes."""
    from custom_components.vigil_alarm.const import EVENT_TYPES

    for lang in LANGUAGES:
        ent = json.loads((ROOT / f"translations/{lang}.json").read_text(encoding="utf-8"))["entity"]
        shown = ent["event"]["alarm_events"]["state_attributes"]["event_type"]["state"]
        assert set(shown) == set(EVENT_TYPES), (lang, set(shown) ^ set(EVENT_TYPES))
        assert ent["sensor"]["last_event"]["state"] == shown
        attrs = ent["alarm_control_panel"]["alarm"]["state_attributes"]
        assert {"intrusion", "fire", "gas", "tamper", "fault"} == set(attrs["cause"]["state"]), lang
        assert {"not_disarmed", "alarm_condition", "sensor_unavailable", "sensor_open"} == set(attrs["refuse_reason"]["state"])
        assert all(v and v != k for k, v in shown.items()), lang  # no raw key left as text
