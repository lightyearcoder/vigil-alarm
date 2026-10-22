"""Do the automations that react to the alarm still run? (0.7.0)

A handler is an automation that reacts to Vigil's events: the Vigil blueprints (flash lights, speech, run actions) or
an automation of your own. At its start and at its end it calls the action `vigil_alarm.handler_report`
(`started`, `done`). With that Vigil can tell three things apart that Home Assistant itself does not:

* the handler never started when it was expected to (only known from a test, see `async_test`),
* the handler started and then stopped without `done`: an error ended it, or it was switched off,
* the handler is fine but still running (a repeat that waits for you to do something): that is never a fault.

Whether it still runs comes from the automation itself: its attribute `current` is the number of runs, and Home
Assistant writes the state again when that changes. So a handler that waits for hours is not "too slow"; only one
whose run is over without `done` is called stalled. A time limit is the fall-back, for a handler Vigil cannot look
at and for a handler that says itself how long it may take (`max_duration`).

Beside that a quiet check: an automation that was made from a Vigil blueprint but is switched off, broken or gone.

Everything is in memory except the list of known handlers: after a restart of Home Assistant a run that was going
is simply gone, which is not a fault.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_STATE_CHANGED
from homeassistant.core import CALLBACK_TYPE, Event, HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .errors import VigilError

if TYPE_CHECKING:
    from .manager import VigilManager

_LOGGER = logging.getLogger(__name__)
STORAGE_VERSION = 1
SIGNAL_HANDLERS = f"{DOMAIN}_handlers_{{}}"
START_TIMEOUT = 60.0  # seconds a handler has to start after a test event
UNREADABLE_LIMIT = 600.0  # a run of an automation Vigil cannot look at: longest it may take
PRACTICE_TEST_LIMIT = 300.0  # the weekly test stops practice mode after this, whatever happens
# The Vigil blueprints that react to the events. The two that arm (on a schedule, when everyone leaves) are not
# handlers: nothing triggers them from Vigil.
BLUEPRINTS = (
    "vigil_alarm/flash_lights_on_alarm.yaml",
    "vigil_alarm/announce_with_speech.yaml",
    "vigil_alarm/run_actions_on_events.yaml",
)
PROBLEM_CODES = ("stalled", "not_started", "disabled", "unavailable", "missing")


@dataclass
class Run:
    run_id: str
    automation: str
    handler: str
    event: str
    started: float
    waits: bool = False
    max_duration: float | None = None
    timer: CALLBACK_TYPE | None = None
    slow_told: bool = False


def _now() -> float:
    return dt_util.utcnow().timestamp()


class HandlerMonitor:
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, manager: VigilManager) -> None:
        self.hass = hass
        self.entry = entry
        self.manager = manager
        self._store: Store[dict[str, Any]] = Store(hass, STORAGE_VERSION, f"{DOMAIN}.handlers.{entry.entry_id}")
        self.known: dict[str, str] = {}  # automation entity id -> name
        self.runs: dict[str, Run] = {}
        self.problems: dict[str, dict[str, str]] = {}  # "<code>:<automation>" -> {...}
        self.last_test: dict[str, Any] | None = None
        self._test: dict[str, Any] | None = None
        self._test_timer: CALLBACK_TYPE | None = None
        self._on_test_done: Callable[[], None] | None = None
        self._unsubs: list[CALLBACK_TYPE] = []
        self._unsubs_once: list[CALLBACK_TYPE] = []  # timers of one test

    # ---------------------------------------------------------- life cycle
    async def async_start(self) -> None:
        stored = await self._store.async_load() or {}
        self.known = dict(stored.get("known") or {})
        self._unsubs.append(
            self.hass.bus.async_listen(EVENT_STATE_CHANGED, self._state_changed, event_filter=self._is_automation)
        )

    @staticmethod
    @callback
    def _is_automation(data: Any) -> bool:
        return str(data.get("entity_id", "")).startswith("automation.")

    @callback
    def stop(self) -> None:
        for unsub in self._unsubs:
            unsub()
        self._unsubs.clear()
        for run in self.runs.values():
            self._cancel_timer(run)
        self.runs.clear()
        self._end_test_timer()
        for unsub in self._unsubs_once:
            unsub()
        self._unsubs_once.clear()

    async def async_remove(self) -> None:
        await self._store.async_remove()

    def _save(self) -> None:
        self._store.async_delay_save(lambda: {"known": self.known}, 10)

    @callback
    def _changed(self) -> None:
        async_dispatcher_send(self.hass, SIGNAL_HANDLERS.format(self.entry.entry_id))

    # ------------------------------------------------------------- reports
    @callback
    def report(self, data: dict[str, Any]) -> None:
        """The action `vigil_alarm.handler_report` of a handler."""
        state = data["state"]
        run_id = data["run_id"]
        automation = data.get("automation") or ""
        name = data.get("handler") or self._friendly(automation) or run_id
        if state == "started":
            self._started(run_id, automation, name, data)
            return
        run = self.runs.pop(run_id, None)
        if run is None:
            return  # a report for a run we never saw (a restart in between): nothing to judge
        self._cancel_timer(run)
        if state == "failed":
            self._problem("stalled", run, str(data.get("error") or "reported as failed"))
        else:
            self._done(run)
        self._changed()

    def _friendly(self, automation: str) -> str:
        state = self.hass.states.get(automation) if automation else None
        return str(state.attributes.get("friendly_name") or "") if state else ""

    def _started(self, run_id: str, automation: str, name: str, data: dict[str, Any]) -> None:
        mode = (self.hass.states.get(automation).attributes.get("mode") if self.hass.states.get(automation) else None)
        if mode == "restart":  # a new run took the place of the one before: that one did not fail
            for old in [r for r in self.runs.values() if r.automation == automation and r.run_id != run_id]:
                self._cancel_timer(self.runs.pop(old.run_id))
        run = Run(
            run_id, automation, name, str(data.get("event") or ""), _now(),
            bool(data.get("waits_for_user")), float(data["max_duration"]) if data.get("max_duration") else None,
        )
        self.runs[run_id] = run
        if automation and automation not in self.known:
            self.known[automation] = name
            self._save()
        self._arm_timer(run)
        if self._test is not None and run.event == "handler_test":
            self._test["answered"].add(automation or name)
        self._changed()

    @callback
    def _done(self, run: Run) -> None:
        for code in ("stalled", "not_started"):
            self.problems.pop(f"{code}:{run.automation or run.handler}", None)
        if run.event == "handler_test" and self._test is not None:
            self._test["result"][run.automation or run.handler] = "ok"
        self._after_test()

    # --------------------------------------------------- is it still going?
    def _readable(self, automation: str) -> bool:
        state = self.hass.states.get(automation) if automation else None
        return state is not None and "current" in state.attributes

    def _arm_timer(self, run: Run) -> None:
        """A limit in time, only where `current` cannot tell, or where the handler gave a maximum itself."""
        if run.waits:
            limit = None  # waits for you: no maximum
        elif run.max_duration:
            limit = run.max_duration
        elif not self._readable(run.automation):
            limit = UNREADABLE_LIMIT
        else:
            limit = None
        if limit is None:
            return

        @callback
        def due(_now: Any) -> None:
            run.timer = None
            if run.run_id not in self.runs:
                return
            if self._readable(run.automation) and run.max_duration:
                if not run.slow_told:  # it still runs, only longer than it said: told once, no repair
                    run.slow_told = True
                    self.manager.publish("handler_slow", handler=run.handler, automation=run.automation,
                                         minutes=max(1, round(limit / 60)))
                return
            self.runs.pop(run.run_id, None)
            self._problem("stalled", run, "timeout")
            self._changed()

        run.timer = async_call_later(self.hass, limit, due)

    @staticmethod
    def _cancel_timer(run: Run) -> None:
        if run.timer:
            run.timer()
            run.timer = None

    @callback
    def _state_changed(self, event: Event) -> None:
        entity_id = event.data["entity_id"]
        mine = [r for r in self.runs.values() if r.automation == entity_id]
        if not mine:
            return
        new = event.data.get("new_state")
        if new is None or new.state == "unavailable":
            return  # reloading: the run is not ours to judge now
        if new.state == "off":
            reason = "switched_off"
        elif int(new.attributes.get("current", 1) or 0) == 0:
            reason = "ended"
        else:
            return  # still running
        for run in mine:
            self.runs.pop(run.run_id, None)
            self._cancel_timer(run)
            self._problem("stalled", run, self._trace_error(entity_id) or reason)
        self._changed()

    # -------------------------------------------------------------- results
    @callback
    def _problem(self, code: str, run: Run | None, detail: str, *, automation: str = "", name: str = "") -> None:
        automation = run.automation if run else automation
        name = run.handler if run else name
        key = f"{code}:{automation or name}"
        fresh = key not in self.problems
        self.problems[key] = {"code": code, "automation": automation, "name": name, "detail": detail}
        if run is not None and run.event == "handler_test" and self._test is not None:
            self._test["result"][automation or name] = "stalled"
        if fresh and code in ("stalled", "not_started"):
            self.manager.publish("handler_stalled", handler=name, automation=automation, reason=code, detail=detail)
        self._after_test()
        self._changed()

    def _trace_error(self, automation: str) -> str:
        """What went wrong in the last run, from the trace Home Assistant keeps. Best effort: it is an internal
        structure, so any surprise gives an empty answer and the fault is reported without a cause."""
        try:
            from homeassistant.components.trace.const import DATA_TRACE

            entity = er.async_get(self.hass).async_get(automation)
            traces = self.hass.data.get(DATA_TRACE, {}).get(f"automation.{entity.unique_id}") if entity else None
            if not traces:
                return ""
            last = list(traces.values())[-1].as_extended_dict()
            for path, elements in (last.get("trace") or {}).items():
                for element in elements:
                    if element.get("error"):
                        return f"{path}: {element['error']}"
            return str(last.get("error") or "")
        except Exception:  # noqa: BLE001
            _LOGGER.debug("Could not read the trace of %s", automation, exc_info=True)
            return ""

    # ----------------------------------------------------------- the checks
    def handler_automations(self) -> dict[str, str]:
        """Every automation that is a handler: from a Vigil blueprint, or one that has reported before."""
        found: dict[str, str] = {}
        try:
            from homeassistant.components.automation import automations_with_blueprint

            for path in BLUEPRINTS:
                for entity_id in automations_with_blueprint(self.hass, path):
                    found[entity_id] = self._friendly(entity_id) or entity_id
        except Exception:  # noqa: BLE001
            _LOGGER.debug("Could not list the blueprint automations", exc_info=True)
        for entity_id, name in self.known.items():
            found.setdefault(entity_id, name)
        return found

    @callback
    def check(self) -> None:
        """The quiet check: is every handler there and switched on?"""
        for key in [k for k, p in self.problems.items() if p["code"] in ("disabled", "unavailable", "missing")]:
            del self.problems[key]
        blueprint = self.handler_automations()
        for entity_id, name in blueprint.items():
            state = self.hass.states.get(entity_id)
            code = None
            if state is None:
                entity = er.async_get(self.hass).async_get(entity_id)
                if entity is None:
                    self.known.pop(entity_id, None)  # taken away on purpose
                    self._save()
                    continue
                code = "disabled" if entity.disabled_by else "missing"
            elif state.state == "off":
                code = "disabled"
            elif state.state == "unavailable":
                code = "unavailable"
            if code:
                self.problems[f"{code}:{entity_id}"] = {"code": code, "automation": entity_id, "name": name, "detail": ""}
        self._changed()

    # ------------------------------------------------------ the handler test
    @callback
    def begin_test(self, *, dry_run: bool) -> None:
        """Send the test event and wait for every handler to answer. Quiet (`dry_run`): the handlers only report."""
        self.check()
        expected = {e: n for e, n in self.handler_automations().items()
                    if (s := self.hass.states.get(e)) is not None and s.state == "on"}
        self._end_test_timer()
        self._test = {"at": _now(), "dry_run": dry_run, "expected": expected, "answered": set(), "result": {}}
        self.manager.publish("handler_test", dry_run=dry_run, handlers=len(expected))
        self._test_timer = async_call_later(self.hass, START_TIMEOUT, self._start_time_up)
        self._unsubs_once.append(async_call_later(self.hass, PRACTICE_TEST_LIMIT, self._test_limit))
        self._after_test()

    @callback
    def start_test(self, *, quiet: bool) -> None:
        """The test. Quiet: the handlers only report. Not quiet: practice mode for the time of the test, so the
        handlers do their work (lights flash) while the siren and Vigil's own messages stay off."""
        if self.testing:
            raise VigilError(translation_domain=DOMAIN, translation_key="handler_test_running")
        started_practice = False
        if not quiet:
            if not self.manager.all_disarmed:
                raise VigilError(translation_domain=DOMAIN, translation_key="handler_test_needs_disarmed")
            if not self.manager.practice.active:
                self.manager.practice.start()
                started_practice = True
        self.begin_test(dry_run=quiet)
        if started_practice:
            def end_practice(*_: Any) -> None:
                self.manager.practice.stop("handler_test")

            self.when_test_done(end_practice)
            self._unsubs_once.append(async_call_later(self.hass, PRACTICE_TEST_LIMIT, end_practice))

    @callback
    def _start_time_up(self, _now: Any) -> None:
        self._test_timer = None
        test = self._test
        if test is None:
            return
        for entity_id, name in test["expected"].items():
            if entity_id not in test["answered"]:
                test["result"][entity_id] = "not_started"
                self._problem("not_started", None, "", automation=entity_id, name=name)
        self._after_test()

    @callback
    def _test_limit(self, _now: Any) -> None:
        """Whatever has not answered by now is counted as not finished; the test must end."""
        test = self._test
        if test is None:
            return
        for entity_id in test["expected"]:
            test["result"].setdefault(entity_id, "running")
        self._finish_test()

    @callback
    def _after_test(self) -> None:
        test = self._test
        if test is None:
            return
        if all(e in test["result"] for e in test["expected"]):
            self._finish_test()

    @callback
    def _finish_test(self) -> None:
        test, self._test = self._test, None
        self._end_test_timer()
        if test is None:
            return
        self.last_test = {
            "at": test["at"], "dry_run": test["dry_run"],
            "result": {self._label(e, test["expected"]): r for e, r in test["result"].items()},
        }
        self.manager.publish("handler_test_done", dry_run=test["dry_run"],
                             ok=sum(1 for r in test["result"].values() if r == "ok"), total=len(test["expected"]))
        if done := self._on_test_done:
            self._on_test_done = None
            done()

    @staticmethod
    def _label(entity_id: str, names: dict[str, str]) -> str:
        return names.get(entity_id) or entity_id

    def _end_test_timer(self) -> None:
        if self._test_timer:
            self._test_timer()
            self._test_timer = None

    @callback
    def when_test_done(self, done: Callable[[], None]) -> None:
        self._on_test_done = done

    @property
    def testing(self) -> bool:
        return self._test is not None

    # ------------------------------------------------------------ reporting
    def status(self) -> dict[str, Any]:
        return {
            "handlers": len(self.handler_automations()),
            "running": len(self.runs),
            "problems": list(self.problems.values()),
            "last_test": self.last_test,
            "testing": self.testing,
        }

    def issues(self) -> dict[str, tuple[str, dict[str, str]]]:
        """For the repairs: id -> (text key, placeholders)."""
        entry_id = self.entry.entry_id
        out: dict[str, tuple[str, dict[str, str]]] = {}
        for key, p in self.problems.items():
            out[f"{entry_id}_handler_{key}"] = (
                f"handler_{p['code']}",
                {"name": p["name"] or p["automation"], "detail": p["detail"] or "-"},
            )
        return out

    def findings(self) -> list[dict[str, Any]]:
        """For the card "Ready for use?"."""
        return [
            {"code": f"handler_{p['code']}", "level": "advice", "go": "log",
             "params": {"name": p["name"] or p["automation"], "detail": p["detail"] or "-"}}
            for p in self.problems.values()
        ]

    def forget(self, automation: str) -> None:
        """An automation that is gone on purpose: stop looking for it."""
        self.known.pop(automation, None)
        for key in [k for k, p in self.problems.items() if p["automation"] == automation]:
            del self.problems[key]
        self._save()
        self._changed()
