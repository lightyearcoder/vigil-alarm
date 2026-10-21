"""Control points such as the ESPHome panel: the source in the log, rejected codes, bypass rules and display attributes."""

from __future__ import annotations

import json

import pytest
from custom_components.vigil_alarm.errors import VigilError as ServiceValidationError

from custom_components.vigil_alarm.const import DOMAIN

from .common import EVENTS, PANEL, make_entry
from .test_integration import _setup


async def _vigil(hass, service, **data):
    await hass.services.async_call(DOMAIN, service, data, blocking=True)


async def test_the_source_is_logged_with_the_user(hass):
    await _setup(hass, make_entry(default_entry_delay=30, exit_delay_home=0))
    await _vigil(hass, "arm", mode="home", code="1234", source="panel garage")
    state = hass.states.get(PANEL)
    assert state.state == "armed_home" and state.attributes["changed_by"] == "Anna"
    assert state.attributes["changed_via"] == "panel garage"
    await _vigil(hass, "disarm", code="5678", source="panel garage")
    assert hass.states.get(PANEL).state == "disarmed"


async def test_without_a_code_the_source_is_the_one_who_armed(hass):
    await _setup(hass, make_entry(code_arm_required=False, exit_delay_home=0))
    await _vigil(hass, "arm", mode="home", source="panel garage")
    assert hass.states.get(PANEL).attributes["changed_by"] is None  # no code, no name
    assert hass.states.get(PANEL).attributes["changed_via"] == "panel garage"
    with pytest.raises(ServiceValidationError, match="code is required"):  # disarming always needs one
        await _vigil(hass, "disarm", source="panel garage")


async def test_a_wrong_code_is_an_event_with_the_source_but_never_the_code(hass):
    await _setup(hass)
    with pytest.raises(ServiceValidationError, match="Invalid code"):
        await _vigil(hass, "arm", mode="home", code="9999", source="panel garage")
    events = hass.states.get(EVENTS).attributes
    assert events["event_type"] == "code_rejected"
    assert events["source"] == "panel garage" and events["action"] == "arm"
    assert "9999" not in json.dumps(dict(events))
    with pytest.raises(ServiceValidationError, match="Invalid code"):
        await _vigil(hass, "bypass", sensor="binary_sensor.living_pir", code="0000", source="panel garage")
    assert hass.states.get(EVENTS).attributes["action"] == "bypass"
    assert hass.states.get(PANEL).state == "disarmed"


async def test_a_mode_that_is_not_enabled_is_refused(hass):
    await _setup(hass, make_entry(modes=["home", "away"]))
    with pytest.raises(ServiceValidationError, match="not enabled"):
        await _vigil(hass, "arm", mode="night", code="1234")
    assert hass.states.get(PANEL).state == "disarmed"


async def test_bypass_asks_for_a_code_only_when_arming_does(hass):
    await _setup(hass, make_entry(code_arm_required=False))
    pir = {"sensor": "binary_sensor.living_pir", "source": "panel garage"}
    await _vigil(hass, "bypass", **pir)  # no code needed, like arming
    assert "Living PIR" in hass.states.get(PANEL).attributes["bypassed_sensors"]
    await _vigil(hass, "unbypass", **pir)
    assert hass.states.get(PANEL).attributes["bypassed_sensors"] == []
    with pytest.raises(ServiceValidationError, match="tamper"):  # a tamper sensor still needs the right,
        await _vigil(hass, "bypass", sensor="binary_sensor.tamper", source="panel garage")  # so a known user


async def test_bypass_needs_a_code_when_arming_does(hass):
    await _setup(hass)  # code_arm_required is on
    with pytest.raises(ServiceValidationError, match="code is required"):
        await _vigil(hass, "bypass", sensor="binary_sensor.living_pir", source="panel garage")


async def test_the_attributes_for_displays(hass):
    """Names of sensors are no longer on the alarm entity: a panel gets them in its profile, when it may show them."""
    from .test_panels import _house, panel_item, profile

    entry = await _house(hass, panel_item(sensor_list="always"))
    hass.states.async_set("binary_sensor.living_pir", "on")
    await hass.async_block_till_done()
    attrs = hass.states.get(PANEL).attributes
    assert attrs["problems_count"] == 0
    for gone in ("open_now_text", "open_sensors_text", "faults_text", "panel_sensors"):
        assert gone not in attrs, gone
    prof = profile(hass).attributes
    assert prof["open_now_text"] == "Living PIR"  # open at all
    assert prof["open_sensors_text"] == "" and prof["open_count"] == 1  # but not in the current mode (disarmed)
    assert prof["faults_text"] == "" and prof["faults_count"] == 0 and prof["problems_count"] == 0
    await _vigil(hass, "arm", mode="home", code="1234")
    hass.states.async_set("binary_sensor.front_door", "on")
    await hass.async_block_till_done()
    assert profile(hass).attributes["open_sensors_text"] == "Front door"  # watching in Home
    lines = {l.split("|")[0]: l.split("|") for l in profile(hass).attributes["sensors"].split("\n")}
    assert lines["Living PIR"] == ["Living PIR", "binary_sensor.living_pir", "open", "1"]
    assert lines["Smoke"][3] == "0" and lines["Tamper"][3] == "1"  # fire/gas can never be bypassed
    assert entry.runtime_data.panels.profile(entry.runtime_data.panels.get("garage"))["modes_mask"] == 7
    # what is most likely to be bypassed comes first: open and bypassable, then open and fire/gas, then the rest
    order = [l.split("|")[0] for l in profile(hass).attributes["sensors"].split("\n")]
    assert order[:2] == ["Front door", "Living PIR"] and order.index("Smoke") > 1 and order[-1] in ("Smoke", "Tamper")
    hass.states.async_set("binary_sensor.smoke", "on")
    await hass.async_block_till_done()
    order = [l.split("|")[0] for l in profile(hass).attributes["sensors"].split("\n")]
    assert order == ["Front door", "Living PIR", "Smoke", "Tamper"]  # open ones first, the unbypassable after them


async def test_the_mode_attribute_and_the_delay_end_are_there_for_displays(hass):
    await _setup(hass)
    await _vigil(hass, "arm", mode="away", code="1234")
    attrs = hass.states.get(PANEL).attributes
    assert attrs["mode"] == "away"
    assert attrs["delay_end"] is None or attrs["delay_end"] > 1_000_000_000  # epoch seconds
    # The seconds left, for displays whose own clock is off.
    assert attrs["delay_left"] is None or 0 <= attrs["delay_left"] <= 120
    assert (attrs["delay_left"] is None) == (attrs["delay_end"] is None)


async def test_too_many_wrong_codes_lock_all_codes_for_a_while(hass, monkeypatch):
    from custom_components.vigil_alarm.manager import VigilManager

    await _setup(hass)
    clock = [1000.0]
    monkeypatch.setattr(VigilManager, "_clock", staticmethod(lambda: clock[0]))
    for _ in range(3):
        with pytest.raises(ServiceValidationError, match="Invalid code|Too many wrong codes"):
            await _vigil(hass, "disarm", code="0000", source="panel garage")
    assert hass.states.get(EVENTS).attributes["event_type"] == "code_rejected"
    with pytest.raises(ServiceValidationError, match="Too many wrong codes"):  # even the right code
        await _vigil(hass, "arm", mode="home", code="1234")
    assert hass.states.get(PANEL).state == "disarmed"
    clock[0] += 5 * 60 + 1
    await _vigil(hass, "arm", mode="home", code="1234")  # open again
    assert hass.states.get(PANEL).state != "disarmed"


async def test_check_code_changes_nothing_and_a_wrong_code_is_a_rejected_try(hass):
    await _setup(hass)
    await _vigil(hass, "check_code", code="1234", source="panel garage")
    assert hass.states.get(PANEL).state == "disarmed"
    with pytest.raises(ServiceValidationError, match="Invalid code"):
        await _vigil(hass, "check_code", code="0000", source="panel garage")
    events = hass.states.get(EVENTS).attributes
    assert events["event_type"] == "code_rejected" and events["action"] == "check_code"
    with pytest.raises(ServiceValidationError, match="code is required"):
        await _vigil(hass, "check_code", source="panel garage")
