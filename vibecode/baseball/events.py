"""Input vocabulary and what each event code means to the simulator."""

from __future__ import annotations

from collections.abc import Mapping
from enum import StrEnum
from types import MappingProxyType

from baseball import outcomes
from baseball.count import Pitch
from baseball.errors import InvalidEventError
from baseball.outcomes import Outcome


class Event(StrEnum):
    BALL = "B"
    STRIKE = "S"
    FOUL = "F"
    SINGLE = "1B"
    DOUBLE = "2B"
    TRIPLE = "3B"
    HOME_RUN = "HR"
    WALK = "BB"
    STRIKEOUT = "K"
    GROUNDOUT = "GO"
    FLYOUT = "FO"

    @classmethod
    def parse(cls, code: str | Event) -> Event:
        try:
            return cls(code.strip().upper())
        except ValueError:
            valid = ", ".join(e.value for e in cls)
            raise InvalidEventError(f"unknown event code {code!r}; expected one of: {valid}") from None


type Action = Pitch | Outcome

# Every event is either a pitch (which updates the count) or a terminal
# outcome (which ends the plate appearance directly).
EVENT_ACTIONS: Mapping[Event, Action] = MappingProxyType(
    {
        Event.BALL: Pitch.BALL,
        Event.STRIKE: Pitch.STRIKE,
        Event.FOUL: Pitch.FOUL,
        Event.SINGLE: outcomes.SINGLE,
        Event.DOUBLE: outcomes.DOUBLE,
        Event.TRIPLE: outcomes.TRIPLE,
        Event.HOME_RUN: outcomes.HOME_RUN,
        Event.WALK: outcomes.WALK,
        Event.STRIKEOUT: outcomes.STRIKEOUT,
        Event.GROUNDOUT: outcomes.BatterOut(),
        Event.FLYOUT: outcomes.BatterOut(),
    }
)

# Fail at import time, not mid-game, if a new Event is added without a mapping.
if _unmapped := set(Event) - EVENT_ACTIONS.keys():
    raise RuntimeError(f"events without an action: {sorted(_unmapped)}")
