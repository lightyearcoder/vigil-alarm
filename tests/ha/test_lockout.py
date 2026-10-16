"""The wrong-code lockout: kept over a restart, a timer per registered control point, one shared for the rest."""

from __future__ import annotations

import pytest
from homeassistant.exceptions import ServiceValidationError

from custom_components.vigil_alarm.const import CODE_LOCK_SECONDS
from custom_components.vigil_alarm.lockout import OTHER, CodeLockout
from custom_components.vigil_alarm.manager import VigilManager

from .common import make_entry
from .test_control_points import _vigil
from .test_integration import _setup


def _lockout(hass, clock, registered=()):
    entry = make_entry()
    return CodeLockout(hass, entry, lambda: clock[0], lambda: set(registered))


async def test_five_wrong_codes_lock_and_the_lock_expires(hass):
    clock = [1000.0]
    lock = _lockout(hass, clock)
    assert [lock.record_failure("phone") for _ in range(4)] == [None] * 4
    assert lock.record_failure("phone") == OTHER
    assert lock.remaining("phone") == CODE_LOCK_SECONDS
    clock[0] += CODE_LOCK_SECONDS + 1
    assert lock.remaining("phone") == 0 and lock.status() == {}


async def test_a_registered_panel_has_its_own_timer(hass):
    clock = [1000.0]
    lock = _lockout(hass, clock, registered={"panel garage", "panel hall"})
    for _ in range(5):
        lock.record_failure("panel garage")
    assert lock.remaining("panel garage") > 0
    assert lock.remaining("panel hall") == 0 and lock.remaining("phone") == 0
    for _ in range(5):
        lock.record_failure("anything")
    assert lock.remaining("phone") > 0 and lock.remaining("another name") > 0  # shared by all unregistered
    assert set(lock.status()) == {"panel garage", OTHER}
    assert lock.clear("panel garage") and lock.remaining("panel garage") == 0
    assert lock.remaining("phone") > 0
    assert lock.clear() and lock.status() == {}


async def test_the_lock_survives_a_restart_and_is_clamped(hass):
    clock = [1000.0]
    lock = _lockout(hass, clock)
    for _ in range(5):
        lock.record_failure(None)
    await hass.async_block_till_done()
    await lock.async_flush()
    again = CodeLockout(hass, make_entry(), lambda: clock[0])
    again._store = lock._store
    await again.async_load()
    assert again.remaining(None) == CODE_LOCK_SECONDS
    await lock._store.async_save({"locked_until": {OTHER: clock[0] + 99999, "old": 5.0, "bad": "x"}})
    clamped = CodeLockout(hass, make_entry(), lambda: clock[0])
    clamped._store = lock._store
    await clamped.async_load()
    assert clamped.status() == {OTHER: CODE_LOCK_SECONDS}


async def test_reloading_vigil_keeps_the_lock_and_tells_the_notifier(hass, monkeypatch):
    entry = await _setup(hass)
    clock = [1000.0]
    monkeypatch.setattr(VigilManager, "_clock", staticmethod(lambda: clock[0]))
    for _ in range(5):
        with pytest.raises(ServiceValidationError, match="Invalid code"):
            await _vigil(hass, "disarm", code="0000", source="phone")
    assert entry.runtime_data.lockout.remaining("phone") > 0
    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    with pytest.raises(ServiceValidationError, match="Too many wrong codes"):
        await _vigil(hass, "arm", mode="home", code="1234")
    clock[0] += CODE_LOCK_SECONDS + 1
    await _vigil(hass, "arm", mode="home", code="1234")
