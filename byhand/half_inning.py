"""Half-inning baseball simulator.

A small, deterministic state machine for one half-inning of baseball.  You
feed it a sequence of plate-appearance events (pitches and outcomes) and it
tracks the count, the baserunners, the outs, and the runs scored, stopping
when the third out is recorded.

------------
All of the game's rules live in one place -- HalfInning.  It is the state
machine, and its small methods are the state transitions.  Events are thin,
typed objects that name what happened and delegate the rules to the inning.
Adding a new kind of event is therefore a local change: register one small
class and nothing else moves.

Baserunning is intentionally simplified: on a hit, every runner and the batter
advance by the number of bases of the hit.  This keeps the model small while
preserving the parts that make baseball a state machine -- the count, forced
walks, and the third out.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class InningOver(Exception):
    """Raised when an event is played after the third out."""


class Bases:
    """The three bases and the runners on them.

    Index 0 is first base, 1 is second, 2 is third.  Each method returns the
    number of runs that scored as a result of the movement.
    """

    def __init__(self) -> None:
        self._occupied = [False, False, False]

    @property
    def state(self) -> tuple[bool, bool, bool]:
        return tuple(self._occupied)

    def advance_all(self, bases_to_take: int) -> int:
        """Advance every runner and the batter by ``bases_to_take`` bases."""
        runs = 0
        moved = [False, False, False]
        for start in range(3):
            if self._occupied[start]:
                runs += self._place(moved, start + bases_to_take)
        runs += self._place(moved, bases_to_take - 1)  # the batter
        self._occupied = moved
        return runs

    def walk_in_batter(self) -> int:
        """Put the batter on first, forcing runners ahead only as needed."""
        runs = 0
        if self._occupied[0]:
            if self._occupied[1]:
                if self._occupied[2]:
                    runs += 1  # bases loaded: the lead runner is forced home
                else:
                    self._occupied[2] = True
            else:
                self._occupied[1] = True
        self._occupied[0] = True
        return runs

    def steal_second(self) -> None:
        """A runner on first steals second, if second is open."""
        if self._occupied[0] and not self._occupied[1]:
            self._occupied[0] = False
            self._occupied[1] = True

    @staticmethod
    def _place(bases: list[bool], destination: int) -> int:
        """Put a runner on destination, or score them if past third."""
        if destination >= 3:
            return 1
        bases[destination] = True
        return 0

    def __str__(self) -> str:
        names = ["1st", "2nd", "3rd"]
        on = [names[i] for i, taken in enumerate(self._occupied) if taken]
        return ", ".join(on) if on else "bases empty"


class HalfInning:
    """One half-inning: the state machine that owns all of the rules."""

    MAX_OUTS = 3

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

    def ball(self) -> None:
        self.balls += 1
        if self.balls == 4:
            self.walk()

    def strike(self) -> None:
        self.strikes += 1
        if self.strikes == 3:
            self.strikeout()

    def foul(self) -> None:
        if self.strikes < 2:
            self.strikes += 1

    # -- outcome transitions (the plate appearance ends) ---------------------

    def hit(self, bases_to_take: int, label: str) -> None:
        self._score(self.bases.advance_all(bases_to_take))
        self._finish_plate_appearance(label)

    def walk(self, label: str = "walk") -> None:
        self._score(self.bases.walk_in_batter())
        self._finish_plate_appearance(label)

    def out(self, label: str) -> None:
        self.outs += 1
        self._finish_plate_appearance(label)
        if self.outs >= self.MAX_OUTS:
            self.over = True

    def strikeout(self) -> None:
        self.out("strikeout")

    def steal(self) -> None:
        # a baserunning play: no out, no run, count and plate appearance unchanged
        self.bases.steal_second()
        self.log.append(self._describe("stolen base"))

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


@event("B")
class Ball(Event):
    def apply(self, inning: HalfInning) -> None:
        inning.ball()


@event("S")
class Strike(Event):
    def apply(self, inning: HalfInning) -> None:
        inning.strike()


@event("F")
class Foul(Event):
    def apply(self, inning: HalfInning) -> None:
        inning.foul()


class Hit(Event):
    """Base class for hits; subclasses set how far the batter advances."""

    bases_to_take = 0
    label = "hit"

    def apply(self, inning: HalfInning) -> None:
        inning.hit(self.bases_to_take, self.label)


@event("1B")
class Single(Hit):
    bases_to_take = 1
    label = "single"


@event("2B")
class Double(Hit):
    bases_to_take = 2
    label = "double"


@event("3B")
class Triple(Hit):
    bases_to_take = 3
    label = "triple"


@event("HR")
class HomeRun(Hit):
    bases_to_take = 4
    label = "home run"


@event("BB")
class Walk(Event):
    def apply(self, inning: HalfInning) -> None:
        inning.walk()


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
    """Run a half-inning from a sequence of event codes.

    sequence may be a string ("1B 1B HR") or a list of codes.  An event
    after the third out raises InningOver.
    """
    tokens = sequence.split() if isinstance(sequence, str) else sequence
    inning = HalfInning()
    for token in tokens:
        inning.play(parse_event(token))
    return inning


def _self_test() -> None:
    # three strikeouts end the inning with nobody scoring
    i = simulate("K K K")
    assert (i.runs, i.outs, i.over) == (0, 3, True)

    # four singles push exactly one run across, bases loaded
    i = simulate("1B 1B 1B 1B")
    assert (i.runs, i.outs, i.bases_occupied()) == (1, 0, (True, True, True))

    # a three-run homer clears two runners and the batter
    i = simulate("1B 1B HR")
    assert (i.runs, i.bases_occupied()) == (3, (False, False, False))

    # a bases-loaded walk forces in a run
    i = simulate("1B 1B 1B BB")
    assert (i.runs, i.bases_occupied()) == (1, (True, True, True))

    # ball four off a full count is a walk
    i = simulate("B B B S S B")
    assert (i.runs, i.outs, i.bases_occupied()) == (0, 0, (True, False, False))

    # a foul with two strikes does not strike the batter out
    i = simulate("S S F F S")
    assert (i.outs, i.over) == (1, False)

    print("all self-tests passed")


def _demo() -> None:
    print("A sample half-inning: 1B, 1B, HR, then three strikeouts\n")
    inning = simulate("1B 1B HR K K K")
    for line in inning.log:
        print("  " + line)
    print("\n  final:", inning.summary())


if __name__ == "__main__":
    _self_test()
    print()
    _demo()