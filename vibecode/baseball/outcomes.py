"""Plate-appearance outcomes.

Each outcome knows how to transform the bases and reports what happened as a
``PlayResult``. To add a new kind of play (sacrifice fly, hit-by-pitch,
double play, ...) implement the ``Outcome`` protocol and map an event to it in
``baseball.events.EVENT_ACTIONS``; the state machine needs no changes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from baseball.bases import Bases


@dataclass(frozen=True, slots=True)
class PlayResult:
    bases: Bases
    runs_scored: int = 0
    outs_recorded: int = 0


class Outcome(Protocol):
    def resolve(self, bases: Bases) -> PlayResult: ...


@dataclass(frozen=True, slots=True)
class Hit:
    """The batter and every runner advance ``bases_gained`` bases."""

    bases_gained: int

    def resolve(self, bases: Bases) -> PlayResult:
        new_bases, runs = bases.advance_all(self.bases_gained)
        return PlayResult(new_bases, runs_scored=runs)


@dataclass(frozen=True, slots=True)
class Walk:
    """The batter is awarded first; runners advance only when forced."""

    def resolve(self, bases: Bases) -> PlayResult:
        new_bases, runs = bases.force_batter_to_first()
        return PlayResult(new_bases, runs_scored=runs)


@dataclass(frozen=True, slots=True)
class BatterOut:
    """The batter is retired; runners hold."""

    def resolve(self, bases: Bases) -> PlayResult:
        return PlayResult(bases, outs_recorded=1)


SINGLE = Hit(1)
DOUBLE = Hit(2)
TRIPLE = Hit(3)
HOME_RUN = Hit(4)
WALK = Walk()
STRIKEOUT = BatterOut()
