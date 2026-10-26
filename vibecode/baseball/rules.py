"""Tunable rule constants.

Putting the thresholds in one object lets variants (e.g. a 3-ball walk for a
youth league) be simulated without touching the state machine.
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Rules:
    balls_for_walk: int = 4
    strikes_for_strikeout: int = 3
    outs_per_inning: int = 3

    def __post_init__(self) -> None:
        for name in ("balls_for_walk", "strikes_for_strikeout", "outs_per_inning"):
            if getattr(self, name) < 1:
                raise ValueError(f"{name} must be at least 1")


DEFAULT_RULES = Rules()
