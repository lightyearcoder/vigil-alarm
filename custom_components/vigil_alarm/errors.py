"""Errors with a message in the language of Home Assistant.

Home Assistant makes the text of an exception from its translation key in English, whatever language is set (its own
code says so), and a standard card shows that text. Vigil has the texts in six languages (translations/*.json), so
these errors say it in the language Home Assistant is set to; a language Vigil does not have falls back to English.
Callers that look at the key (a frontend that translates by key) get it as before.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .languages import DEFAULT_LANGUAGE, language_of
from .messages import MODE_NAMES

_DIR = Path(__file__).parent / "translations"
_MESSAGES: dict[str, dict[str, str]] = {}  # language -> key -> text, read once (not while an error is raised)
_language = DEFAULT_LANGUAGE


def _read(language: str) -> dict[str, str]:
    try:
        raw = json.loads((_DIR / f"{language}.json").read_text(encoding="utf-8"))
        return {k: v["message"] for k, v in raw.get("exceptions", {}).items() if isinstance(v, dict) and "message" in v}
    except (OSError, ValueError):
        return {}


async def async_prepare(hass: HomeAssistant) -> None:
    """Read the texts of the language Home Assistant is set to (and English), outside the event loop."""
    global _language
    _language = language_of(hass.config.language)
    for language in {DEFAULT_LANGUAGE, _language}:
        if language not in _MESSAGES:
            _MESSAGES[language] = await hass.async_add_executor_job(_read, language)


class VigilError(HomeAssistantError):
    """A refusal whose message is in the language of Home Assistant.

    Not a ServiceValidationError on purpose: for that one Home Assistant puts "Validation error: " before the text of
    the message, and the refusal is already clear (a card shows it in red)."""

    def __str__(self) -> str:
        if self._message:
            return self._message
        key = self.translation_key
        if self.generate_message and key:
            text = _MESSAGES.get(_language, {}).get(key) or _MESSAGES.get(DEFAULT_LANGUAGE, {}).get(key)
            if text:
                values: dict[str, Any] = dict(self.translation_placeholders or {})
                # A mode is named as the person knows it ("Aangepast"), not by its internal name ("custom").
                names = MODE_NAMES.get(_language, MODE_NAMES[DEFAULT_LANGUAGE])
                if values.get("mode") in names:
                    values["mode"] = names[values["mode"]]
                try:
                    self._message = text.format(**values)
                except (KeyError, IndexError, ValueError):
                    self._message = text
                return self._message
        return super().__str__()
