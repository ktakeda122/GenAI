"""The half-inning state machine and the ``simulate`` entry point."""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from baseball.bases import Bases
from baseball.count import Count, Pitch
from baseball.errors import InningOverError
from baseball.events import EVENT_ACTIONS, Action, Event
from baseball.outcomes import Outcome
from baseball.rules import DEFAULT_RULES, Rules


class HalfInning:
    """Mutable state for one half-inning, advanced one event at a time."""

    def __init__(
        self,
        rules: Rules = DEFAULT_RULES,
        actions: Mapping[Event, Action] = EVENT_ACTIONS,
    ) -> None:
        self._rules = rules
        self._actions = actions
        self._count = Count()
        self._bases = Bases.empty()
        self._outs = 0
        self._runs = 0

    @property
    def runs(self) -> int:
        return self._runs

    @property
    def outs(self) -> int:
        return self._outs

    @property
    def over(self) -> bool:
        return self._outs >= self._rules.outs_per_inning

    @property
    def count(self) -> Count:
        return self._count

    def bases_occupied(self) -> tuple[bool, bool, bool]:
        first, second, third = self._bases.occupied
        return first, second, third

    def process(self, event: Event | str) -> None:
        """Apply a single event. Raises ``InningOverError`` once the inning has ended."""
        if self.over:
            raise InningOverError(f"cannot process {event!r}: the half-inning is over")

        match self._actions[Event.parse(event)]:
            case Pitch() as pitch:
                self._count = self._count.after(pitch, self._rules)
                if (forced := self._count.outcome(self._rules)) is not None:
                    self._end_plate_appearance(forced)
            case outcome:
                self._end_plate_appearance(outcome)

    def process_all(self, events: Iterable[Event | str]) -> None:
        for event in events:
            self.process(event)

    def _end_plate_appearance(self, outcome: Outcome) -> None:
        result = outcome.resolve(self._bases)
        self._bases = result.bases
        self._runs += result.runs_scored
        self._outs += result.outs_recorded
        self._count = Count()

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}(runs={self.runs}, outs={self.outs}, "
            f"count={self._count.balls}-{self._count.strikes}, "
            f"bases={self.bases_occupied()}, over={self.over})"
        )


def simulate(
    sequence: str | Iterable[Event | str],
    rules: Rules = DEFAULT_RULES,
) -> HalfInning:
    """Run a sequence of events and return the resulting half-inning.

    ``sequence`` is either a whitespace-separated string (``"1B 1B HR"``) or
    an iterable of event codes.
    """
    events = sequence.split() if isinstance(sequence, str) else sequence
    inning = HalfInning(rules)
    inning.process_all(events)
    return inning
