"""The languages Vigil speaks: one list for the integration, with the few words the code itself needs.

The texts live elsewhere (translations/*.json, messages.py, the panel and card JavaScript, and the touch panel
firmware). A language that is not here falls back to English.
"""

from __future__ import annotations

LANGUAGES = ("en", "nl", "de", "fr", "it", "es")
DEFAULT_LANGUAGE = "en"


def language_of(value: object) -> str:
    """'nl', 'nl-NL', 'de_AT' or anything else -> one of LANGUAGES (English when it is not one of them)."""
    code = str(value or "").replace("_", "-").lower().split("-")[0]
    return code if code in LANGUAGES else DEFAULT_LANGUAGE


# The names of the two groups a new installation starts with: doors and windows, and motion.
GROUP_NAMES = {
    "en": {"contacts": "Perimeter", "motion": "Interior"},
    "nl": {"contacts": "Buitenschil", "motion": "Binnen"},
    "de": {"contacts": "Außenhaut", "motion": "Innenraum"},
    "fr": {"contacts": "Périmètre", "motion": "Intérieur"},
    "it": {"contacts": "Perimetro", "motion": "Interni"},
    "es": {"contacts": "Perímetro", "motion": "Interior"},
}

# "Front door (tamper)": the word in the name of the tamper sensor that Vigil adds next to a sensor.
TAMPER_WORD = {"en": "tamper", "nl": "sabotage", "de": "Sabotage", "fr": "sabotage", "it": "manomissione", "es": "sabotaje"}

# After the last alarm on a touch panel: "(false alarm)".
FALSE_ALARM = {
    "en": "false alarm", "nl": "vals alarm", "de": "Fehlalarm", "fr": "fausse alerte", "it": "falso allarme",
    "es": "falsa alarma",
}
