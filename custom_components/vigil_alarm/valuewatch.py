"""A sensor that watches a number: a freezer that gets too warm, a room that gets too cold, a mains voltage that drops.

The sensor entity holds a number (temperature, voltage, power, current). It has a lower and/or an upper limit and a
time. A value outside the limits for longer than that time counts as an open sensor (a technical alarm, like water);
a value back inside the limits closes it at once. No value at all (`unavailable`, `unknown`, not a number) is an
unavailable sensor and follows the choice made for those, the same as for any other sensor.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping

from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers.event import async_call_later

from .const import CONF_FOR, CONF_MAX_VALUE, CONF_MIN_VALUE


@dataclass(frozen=True)
class Range:
    low: float | None = None
    high: float | None = None
    hold: float = 0.0  # seconds outside the limits before it counts

    @classmethod
    def from_data(cls, data: Mapping[str, Any]) -> "Range | None":
        low, high = data.get(CONF_MIN_VALUE), data.get(CONF_MAX_VALUE)
        if low in (None, "") and high in (None, ""):
            return None
        return cls(
            None if low in (None, "") else float(low),
            None if high in (None, "") else float(high),
            float(data.get(CONF_FOR) or 0),
        )

    def classify(self, state: Any) -> str:
        """"open" (outside the limits), "closed" (inside) or "unavailable" (no number)."""
        if state is None:
            return "unavailable"
        try:
            value = float(state.state)
        except (TypeError, ValueError):
            return "unavailable"
        if value != value:  # NaN
            return "unavailable"
        if (self.low is not None and value < self.low) or (self.high is not None and value > self.high):
            return "open"
        return "closed"


class ValueWatch:
    """The time part: a value outside the limits is only passed on as open after `hold` seconds."""

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self._timers: dict[str, CALLBACK_TYPE] = {}
        self._open: set[str] = set()

    def apply(self, sid: str, rng: Range, raw: str, time_up: Callable[[], None]) -> str | None:
        """The value to give the engine now, or None while the sensor is waiting out its time.

        `time_up` is called when the time is over; it must look at the state again and call `confirm`."""
        if raw != "open":
            self.cancel(sid)
            self._open.discard(sid)
            return raw
        if sid in self._open or rng.hold <= 0:
            self._open.add(sid)
            return "open"
        if sid not in self._timers:  # the time runs from the first value outside the limits, not from the last
            @callback
            def due(_now: Any) -> None:
                self._timers.pop(sid, None)
                time_up()

            self._timers[sid] = async_call_later(self.hass, rng.hold, due)
        return None

    def confirm(self, sid: str) -> None:
        self._open.add(sid)

    def cancel(self, sid: str) -> None:
        if timer := self._timers.pop(sid, None):
            timer()

    def shutdown(self) -> None:
        for timer in self._timers.values():
            timer()
        self._timers.clear()
        self._open.clear()
