"""Release 0.5.5: the tamper entity field is offered for the 24-hour sensor types too."""

from __future__ import annotations

from custom_components.vigil_alarm.panel import form_schema


def test_the_tamper_entity_field_is_there_for_the_24_hour_types():
    fields = {f["key"]: f for f in form_schema(["home", "away", "night"])["sensor"]}
    shown = fields["tamper_entity"]["show_if"]["cls"]
    for cls in ("intrusion", "fire", "gas", "water", "alarm24", "silent24"):
        assert cls in shown
    assert "tamper" not in shown  # a tamper sensor has no tamper sensor of its own
    assert {"alarm24", "silent24"} <= set(fields["cls"]["options"])
