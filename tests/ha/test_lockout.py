"""The wrong-code lockout in steps: kept over a restart, a timer per registered control point, one shared for the rest."""

from __future__ import annotations

import pytest
from custom_components.vigil_alarm.errors import VigilError as ServiceValidationError

from custom_components.vigil_alarm.const import LOCK_DEFAULTS
from custom_components.vigil_alarm.lockout import OTHER, CodeLockout, Locked
from custom_components.vigil_alarm.manager import VigilManager

from .common import make_entry
from .test_control_points import _vigil
from .test_integration import _setup

MIN = 60.0


def _lockout(hass, clock, registered=(), **settings):
    entry = make_entry(**settings)
    return CodeLockout(hass, entry, lambda: clock[0], lambda: set(registered))


def _fail(lock, source, times, bucket=None):
    return [lock.record_failure(source, bucket=bucket) for _ in range(times)]


async def test_the_lock_goes_in_steps_and_the_last_one_is_permanent(hass):
    clock = [1000.0]
    lock = _lockout(hass, clock, registered={"garage"})
    d = LOCK_DEFAULTS
    # first lock: 3 wrong codes, 5 minutes
    assert _fail(lock, "garage", d["lock_tries_1"] - 1) == [None, None]
    assert lock.record_failure("garage") == Locked("garage", d["lock_wait_1"])
    assert lock.remaining("garage") == d["lock_wait_1"] * MIN and lock.refusal("garage") == "code_locked"
    clock[0] += d["lock_wait_1"] * MIN + 1
    assert lock.refusal("garage") is None
    # second lock: 2 more wrong codes, 15 minutes
    assert _fail(lock, "garage", d["lock_tries_2"] - 1) == [None]
    assert lock.record_failure("garage") == Locked("garage", d["lock_wait_2"])
    clock[0] += d["lock_wait_2"] * MIN + 1
    # third lock: 2 more, 60 minutes
    assert _fail(lock, "garage", d["lock_tries_3"] - 1) == [None]
    assert lock.record_failure("garage") == Locked("garage", d["lock_wait_3"])
    clock[0] += d["lock_wait_3"] * MIN + 1
    assert lock.refusal("garage") is None
    # then 1 more wrong code and it is locked for good
    assert lock.record_failure("garage") == Locked("garage", None)
    assert lock.is_permanent("garage") and lock.refusal("garage") == "code_locked_permanent"
    clock[0] += 10 * 24 * 3600
    assert lock.refusal("garage") == "code_locked_permanent" and lock.permanent() == {"garage"}
    assert lock.clear("garage") is True and lock.refusal("garage") is None and lock.permanent() == set()
    # the steps start again from the first after an unlock
    assert _fail(lock, "garage", d["lock_tries_1"])[-1] == Locked("garage", d["lock_wait_1"])


async def test_a_right_code_starts_all_over(hass):
    clock = [1000.0]
    lock = _lockout(hass, clock)
    assert _fail(lock, "phone", 2) == [None, None]
    lock.record_success("phone")
    assert _fail(lock, "phone", 2) == [None, None]  # the count is zero again, so still no lock
    assert lock.record_failure("phone") == Locked(OTHER, LOCK_DEFAULTS["lock_wait_1"])
    clock[0] += LOCK_DEFAULTS["lock_wait_1"] * MIN + 1
    assert _fail(lock, "phone", 1) == [None]  # second step wants 2
    lock.record_success("phone")  # back to the first step: 3 wrong codes, first wait
    assert _fail(lock, "phone", 3)[-1] == Locked(OTHER, LOCK_DEFAULTS["lock_wait_1"])


async def test_the_numbers_are_settings(hass):
    clock = [1000.0]
    lock = CodeLockout(
        hass, make_entry(lock_tries_1=1, lock_wait_1=2, lock_tries_2=1, lock_wait_2=7, lock_tries_3=1, lock_wait_3=9,
                         lock_tries_4=2), lambda: clock[0], lambda: {"x"})
    assert lock.record_failure("x") == Locked("x", 2)
    clock[0] += 2 * MIN + 1
    assert lock.record_failure("x") == Locked("x", 7)
    clock[0] += 7 * MIN + 1
    assert lock.record_failure("x") == Locked("x", 9)
    clock[0] += 9 * MIN + 1
    assert lock.record_failure("x") is None
    assert lock.record_failure("x") == Locked("x", None)


async def test_the_shared_timer_never_locks_for_good(hass):
    clock = [1000.0]
    lock = _lockout(hass, clock)
    d = LOCK_DEFAULTS
    for tries, wait in ((d["lock_tries_1"], d["lock_wait_1"]), (d["lock_tries_2"], d["lock_wait_2"]),
                        (d["lock_tries_3"], d["lock_wait_3"])):
        assert _fail(lock, "phone", tries)[-1] == Locked(OTHER, wait)
        clock[0] += wait * MIN + 1
    result = _fail(lock, "phone", d["lock_tries_4"])[-1]
    assert result == Locked(OTHER, d["lock_wait_3"])  # nobody could unlock it: the longest wait again
    assert lock.permanent() == set()


async def test_a_registered_panel_has_its_own_timer(hass):
    clock = [1000.0]
    lock = _lockout(hass, clock, registered={"panel garage", "panel hall"})
    _fail(lock, "panel garage", 3)
    assert lock.remaining("panel garage") > 0
    assert lock.remaining("panel hall") == 0 and lock.remaining("phone") == 0
    _fail(lock, "anything", 3)
    assert lock.remaining("phone") > 0 and lock.remaining("another name") > 0  # shared by all unregistered
    assert set(lock.status()) == {"panel garage", OTHER}
    assert lock.clear("panel garage") and lock.remaining("panel garage") == 0
    assert lock.remaining("phone") > 0
    assert lock.clear() and lock.status() == {}


async def test_the_lock_the_step_and_a_permanent_lock_survive_a_restart(hass):
    clock = [1000.0]
    lock = _lockout(hass, clock, registered={"garage"})
    _fail(lock, "garage", 3)  # first lock, now in step 1
    _fail(lock, None, 1)  # one wrong code at "other"
    await hass.async_block_till_done()
    await lock.async_flush()

    def reopen():
        again = CodeLockout(hass, make_entry(), lambda: clock[0], lambda: {"garage"})
        again._store = lock._store
        return again

    again = reopen()
    await again.async_load()
    assert again.remaining("garage") == LOCK_DEFAULTS["lock_wait_1"] * MIN
    clock[0] += LOCK_DEFAULTS["lock_wait_1"] * MIN + 1
    # it is still in the second step: 2 wrong codes, not 3
    assert _fail(again, "garage", 2)[-1] == Locked("garage", LOCK_DEFAULTS["lock_wait_2"])
    # and "other" remembered its one wrong code
    assert _fail(again, None, 2)[-1] == Locked(OTHER, LOCK_DEFAULTS["lock_wait_1"])
    # a permanent lock is kept, and a stored end far away is cut back
    again._permanent.add("garage")
    await again.async_flush()
    clamped = reopen()
    await clamped.async_load()
    assert clamped.is_permanent("garage")
    await lock._store.async_save({"locked_until": {OTHER: clock[0] + 999999, "old": 5.0, "bad": "x"}})
    clamped = reopen()
    await clamped.async_load()
    assert clamped.status() == {OTHER: LOCK_DEFAULTS["lock_wait_3"] * MIN}


async def test_reloading_vigil_keeps_the_lock_and_a_permanent_lock_is_reported(hass, monkeypatch):
    entry = await _setup(hass)
    clock = [1000.0]
    monkeypatch.setattr(VigilManager, "_clock", staticmethod(lambda: clock[0]))
    for _ in range(3):
        with pytest.raises(ServiceValidationError, match="Invalid code|Too many wrong codes"):
            await _vigil(hass, "disarm", code="0000", source="phone")
    assert entry.runtime_data.lockout.remaining("phone") > 0
    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    with pytest.raises(ServiceValidationError, match="Too many wrong codes"):
        await _vigil(hass, "arm", mode="home", code="1234")
    clock[0] += LOCK_DEFAULTS["lock_wait_1"] * MIN + 1
    await _vigil(hass, "arm", mode="home", code="1234")  # a right code: the step starts over
    assert entry.runtime_data.lockout._step.get(OTHER, 0) == 0
