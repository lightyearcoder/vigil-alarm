"""0.6.10: errors say it in the language of Home Assistant (its own text is always English)."""

from __future__ import annotations

import pytest
from homeassistant.setup import async_setup_component
from custom_components.vigil_alarm.errors import VigilError as ServiceValidationError

from .test_integration import _call, _setup


@pytest.mark.parametrize(("language", "text"), [
    ("nl", "Modus Weg is door u niet toegestaan om in te schakelen"),
    ("de", "Der Modus Abwesend darf von Ihnen nicht scharfgeschaltet werden"),
    ("fr", "Le mode Absent ne peut pas être activé par vous"),
    ("en", "Mode Away is not allowed to be armed by you"),
    ("xx", "Mode Away is not allowed to be armed by you"),  # a language Vigil does not have: English
])
async def test_the_message_is_in_the_language_of_home_assistant(hass, language, text):
    hass.config.language = language
    await _setup(hass)
    with pytest.raises(ServiceValidationError) as err:
        await _call(hass, "alarm_arm_away", code="5678")  # Bob may only arm at home
    assert text in str(err.value)
    assert "Bob" not in str(err.value)  # no name of a user, and the mode as the person knows it ("Weg", not "away")
    # the key stays, for a frontend that translates by key
    assert err.value.translation_key == "mode_not_allowed" and err.value.translation_domain == "vigil_alarm"


async def test_the_message_has_no_validation_error_in_front_of_it(hass, hass_ws_client):
    """0.6.10: Home Assistant puts "Validation error: " before a ServiceValidationError; a refusal of Vigil says only
    what is wrong (a card shows it in red), also over the websocket a card uses."""
    hass.config.language = "nl"
    await _setup(hass)
    assert await async_setup_component(hass, "websocket_api", {})
    client = await hass_ws_client(hass)
    await client.send_json({"id": 1, "type": "call_service", "domain": "alarm_control_panel", "service": "alarm_arm_away",
                            "target": {"entity_id": "alarm_control_panel.vigil_alarm"}, "service_data": {"code": "5678"}})
    reply = await client.receive_json()
    assert reply["success"] is False
    assert reply["error"]["message"] == "Modus Weg is door u niet toegestaan om in te schakelen."
    assert reply["error"]["translation_key"] == "mode_not_allowed"
