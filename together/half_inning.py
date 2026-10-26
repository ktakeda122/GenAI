"""Half-inning baseball simulator -- minimal seed.

This is the STARTING POINT for building the simulator together with an AI
assistant.  It is deliberately small: it handles only strikeouts, groundouts,
and home runs.  But it already establishes the full architecture that every
new feature must follow -- see CLAUDE.md.

Architecture in one breath:
  * All rules live in HalfInning -- it is the state machine, its methods are
    the transitions.
  * Events are thin, typed objects that just delegate to a HalfInning method.
  * Bases owns runner bookkeeping; nothing else touches base occupancy.
  * New event codes register themselves through the @event decorator.

Public API (keep stable):
  simulate(sequence) -> HalfInning, exposing .runs, .outs, .over,
  and .bases_occupied() -> (first, second, third).
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class InningOver(Exception):
    """Raised when an event is played after the third out."""


class Bases:
    """The three bases and the runners on them (index 0=first, 1=second, 2=third).

    The seed only needs to count runners (for a home run) and clear them.
    Richer movement -- advancing everyone on a hit, forcing runners on a walk --
    is a feature to be added later, and belongs here, not in HalfInning.
    """

    def __init__(self) -> None:
        self._occupied = [False, False, False]

    @property
    def state(self) -> tuple[bool, bool, bool]:
        return tuple(self._occupied)

    def runners_on(self) -> int:
        return sum(self._occupied)

    def clear(self) -> None:
        self._occupied = [False, False, False]

    def walk_in_batter(self) -> int:
        """Put the batter on first, forcing runners only as needed; return runs forced in."""
        for i in range(3):
            if not self._occupied[i]:
                self._occupied[i] = True
                return 0
        return 1  # bases loaded: the walk forces in one run

    def advance_all(self, bases: int) -> int:
        """Advance every runner and the batter by `bases`; return runs scored."""
        starts = self._runner_starts()
        self._occupied = [False, False, False]
        return sum(self._place_runner(start + bases) for start in starts)

    def steal_second(self) -> None:
        """Move the runner on first to second, if first is taken and second is empty."""
        if self._occupied[0] and not self._occupied[1]:
            self._occupied[0], self._occupied[1] = False, True

    def _runner_starts(self) -> list[int]:
        """Start positions to advance: each current runner, plus the batter at home (-1)."""
        return [i for i, taken in enumerate(self._occupied) if taken] + [-1]

    def _place_runner(self, dest: int) -> int:
        """Occupy base `dest`, or score the runner (return 1) if they pass third."""
        if dest >= 3:
            return 1
        self._occupied[dest] = True
        return 0

    def __str__(self) -> str:
        names = ["1st", "2nd", "3rd"]
        on = [names[i] for i, taken in enumerate(self._occupied) if taken]
        return ", ".join(on) if on else "bases empty"


class HalfInning:
    """One half-inning: the state machine that owns all of the rules."""

    MAX_OUTS = 3
    STRIKES_FOR_OUT = 3
    BALLS_FOR_WALK = 4

    def __init__(self) -> None:
        self.balls = 0
        self.strikes = 0
        self.outs = 0
        self.runs = 0
        self.bases = Bases()
        self.over = False
        self.log: list[str] = []

    # -- public entry point --------------------------------------------------

    def play(self, event: Event) -> None:
        if self.over:
            raise InningOver("the half-inning already has three outs")
        event.apply(self)

    # -- pitch transitions (the plate appearance continues) ------------------

    def strike(self) -> None:
        self.strikes += 1
        if self.strikes == self.STRIKES_FOR_OUT:
            self.strikeout()

    def ball(self) -> None:
        self.balls += 1
        if self.balls == self.BALLS_FOR_WALK:
            self.walk()

    def foul(self) -> None:
        if self.strikes < self.STRIKES_FOR_OUT - 1:
            self.strike()

    # -- baserunning transitions (the plate appearance continues) ------------

    def steal(self) -> None:
        self.bases.steal_second()

    # -- outcome transitions (the plate appearance ends) ---------------------

    def hit(self, bases: int, label: str) -> None:
        self._score(self.bases.advance_all(bases))
        self._finish_plate_appearance(label)

    def home_run(self) -> None:
        self.hit(4, "home run")

    def walk(self) -> None:
        self._score(self.bases.walk_in_batter())
        self._finish_plate_appearance("walk")

    def out(self, label: str) -> None:
        self.outs += 1
        self._finish_plate_appearance(label)
        if self.outs >= self.MAX_OUTS:
            self.over = True

    def strikeout(self) -> None:
        self.out("strikeout")

    # -- helpers -------------------------------------------------------------

    def _score(self, runs: int) -> None:
        self.runs += runs

    def _finish_plate_appearance(self, label: str) -> None:
        self.balls = 0
        self.strikes = 0
        self.log.append(self._describe(label))

    def _describe(self, label: str) -> str:
        return f"{label}: {self.outs} out(s), {self.runs} run(s), {self.bases}"

    def bases_occupied(self) -> tuple[bool, bool, bool]:
        """Public view of the runners: (first, second, third)."""
        return self.bases.state

    def summary(self) -> str:
        status = "inning over" if self.over else "in progress"
        return f"{self.runs} run(s), {self.outs} out(s) ({status})"


EVENT_TYPES: dict[str, type[Event]] = {}


def event(code: str):
    """Register an event class under the short code the parser reads."""

    def register(cls: type[Event]) -> type[Event]:
        cls.code = code
        EVENT_TYPES[code] = cls
        return cls

    return register


class Event(ABC):
    """A single thing that can happen during a plate appearance."""

    code = ""

    @abstractmethod
    def apply(self, inning: HalfInning) -> None:
        ...


@event("S")
class Strike(Event):
    def apply(self, inning: HalfInning) -> None:
        inning.strike()


@event("K")
class Strikeout(Event):
    def apply(self, inning: HalfInning) -> None:
        inning.strikeout()


@event("GO")
class Groundout(Event):
    def apply(self, inning: HalfInning) -> None:
        inning.out("groundout")


@event("FO")
class Flyout(Event):
    def apply(self, inning: HalfInning) -> None:
        inning.out("flyout")


@event("1B")
class Single(Event):
    def apply(self, inning: HalfInning) -> None:
        inning.hit(1, "single")


@event("2B")
class Double(Event):
    def apply(self, inning: HalfInning) -> None:
        inning.hit(2, "double")


@event("3B")
class Triple(Event):
    def apply(self, inning: HalfInning) -> None:
        inning.hit(3, "triple")


@event("HR")
class HomeRun(Event):
    def apply(self, inning: HalfInning) -> None:
        inning.home_run()


@event("B")
class Ball(Event):
    def apply(self, inning: HalfInning) -> None:
        inning.ball()


@event("BB")
class Walk(Event):
    def apply(self, inning: HalfInning) -> None:
        inning.walk()


@event("F")
class Foul(Event):
    def apply(self, inning: HalfInning) -> None:
        inning.foul()


@event("SB")
class StolenBase(Event):
    def apply(self, inning: HalfInning) -> None:
        inning.steal()


def parse_event(token: str) -> Event:
    try:
        return EVENT_TYPES[token]()
    except KeyError:
        raise ValueError(f"unknown event code: {token!r}") from None


def simulate(sequence: str | list[str]) -> HalfInning:
    """Run a half-inning from a sequence of event codes (string or list)."""
    tokens = sequence.split() if isinstance(sequence, str) else sequence
    inning = HalfInning()
    for token in tokens:
        inning.play(parse_event(token))
    return inning


def _self_test() -> None:
    # a solo home run scores exactly one
    i = simulate("HR")
    assert (i.runs, i.outs, i.bases_occupied()) == (1, 0, (False, False, False))

    # three strikeouts end the inning with nobody scoring
    i = simulate("K K K")
    assert (i.runs, i.outs, i.over) == (0, 3, True)

    # four singles load the bases and force in exactly one run
    i = simulate("1B 1B 1B 1B")
    assert (i.runs, i.outs, i.bases_occupied()) == (1, 0, (True, True, True))

    # two singles then a home run clears the bases for three runs
    i = simulate("1B 1B HR")
    assert (i.runs, i.bases_occupied()) == (3, (False, False, False))

    # a walk with the bases loaded forces in exactly one run
    i = simulate("1B 1B 1B BB")
    assert (i.runs, i.bases_occupied()) == (1, (True, True, True))

    # ball four from the count walks the batter to first
    i = simulate("B B B S S B")
    assert (i.runs, i.outs, i.bases_occupied()) == (0, 0, (True, False, False))

    # a bare walk puts the batter on first
    i = simulate("BB")
    assert (i.runs, i.bases_occupied()) == (0, (True, False, False))

    # two-strike fouls never make the third strike; the final strike ends it
    i = simulate("S S F F S")
    assert (i.outs, i.over) == (1, False)

    # a foul at two strikes does NOT strike the batter out
    i = simulate("S S F")
    assert (i.outs, i.over) == (0, False)

    # fouls below two strikes count as strikes, so this is a strikeout
    i = simulate("F F S")
    assert i.outs == 1

    # a flyout is a single out
    i = simulate("FO")
    assert (i.runs, i.outs, i.over) == (0, 1, False)

    # three flyouts end the half-inning
    i = simulate("FO FO FO")
    assert (i.outs, i.over) == (3, True)

    # flyouts don't advance runners: the single's runner stays on first
    i = simulate("1B FO FO FO")
    assert (i.runs, i.outs, i.over, i.bases_occupied()) == (0, 3, True, (True, False, False))

    # three strikes is a single strikeout
    i = simulate("S S S")
    assert (i.outs, i.over) == (1, False)

    # three groundouts end the inning
    i = simulate("GO GO GO")
    assert (i.outs, i.over) == (3, True)

    # a steal moves the runner from first to second
    i = simulate("1B SB")
    assert (i.runs, i.outs, i.bases_occupied()) == (0, 0, (False, True, False))

    # a steal with nobody on first does nothing
    i = simulate("SB")
    assert i.bases_occupied() == (False, False, False)

    # a steal is blocked when second is occupied
    i = simulate("1B 1B SB")
    assert i.bases_occupied() == (True, True, False)

    # a steal leaves the count alone: three more strikes is one strikeout
    i = simulate("1B SB S S S")
    assert (i.outs, i.bases_occupied()) == (1, (False, True, False))

    print("seed self-tests passed")


if __name__ == "__main__":
    _self_test()