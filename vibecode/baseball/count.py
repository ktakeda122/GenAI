"""Ball-strike count and the pitches that change it."""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum, auto

from baseball.outcomes import STRIKEOUT, WALK, Outcome
from baseball.rules import Rules


class Pitch(Enum):
    """A pitch that changes the count without, by itself, ending the plate appearance."""

    BALL = auto()
    STRIKE = auto()
    FOUL = auto()


@dataclass(frozen=True, slots=True)
class Count:
    balls: int = 0
    strikes: int = 0

    def after(self, pitch: Pitch, rules: Rules) -> Count:
        """Return the count that results from ``pitch``."""
        match pitch:
            case Pitch.BALL:
                return replace(self, balls=self.balls + 1)
            case Pitch.STRIKE:
                return replace(self, strikes=self.strikes + 1)
            case Pitch.FOUL:
                # A foul can never be the strike that completes a strikeout.
                if self.strikes < rules.strikes_for_strikeout - 1:
                    return replace(self, strikes=self.strikes + 1)
                return self

    def outcome(self, rules: Rules) -> Outcome | None:
        """Return the plate-appearance outcome this count forces, if any."""
        if self.balls >= rules.balls_for_walk:
            return WALK
        if self.strikes >= rules.strikes_for_strikeout:
            return STRIKEOUT
        return None
