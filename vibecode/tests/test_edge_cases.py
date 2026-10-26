"""Edge cases and component-level tests beyond the specification."""

from dataclasses import dataclass
from itertools import product

import pytest

from baseball import (
    EVENT_ACTIONS,
    Bases,
    Count,
    Event,
    HalfInning,
    InningOverError,
    InvalidEventError,
    Pitch,
    PlayResult,
    Rules,
    SimulationError,
    simulate,
)

# --- The count -------------------------------------------------------------


class TestCount:
    def test_foul_adds_a_strike_below_two_strikes(self) -> None:
        inning = simulate("F F")
        assert inning.count == Count(balls=0, strikes=2)
        assert inning.outs == 0

    def test_foul_never_completes_a_strikeout(self) -> None:
        inning = simulate("S S" + " F" * 10)
        assert inning.count == Count(balls=0, strikes=2)
        assert inning.outs == 0

    def test_fouls_then_strike_is_a_strikeout(self) -> None:
        assert simulate("F F S").outs == 1

    def test_balls_do_not_affect_strikes(self) -> None:
        inning = simulate("B B B S S F")
        assert inning.count == Count(balls=3, strikes=2)

    def test_full_count_walk(self) -> None:
        inning = simulate("B S B S B F B")
        assert inning.bases_occupied() == (True, False, False)
        assert inning.count == Count()

    def test_full_count_strikeout(self) -> None:
        inning = simulate("B B B S S S")
        assert inning.outs == 1
        assert inning.bases_occupied() == (False, False, False)

    @pytest.mark.parametrize("terminal", ["1B", "2B", "3B", "HR", "BB", "K", "GO", "FO"])
    def test_count_resets_after_every_terminal_event(self, terminal: str) -> None:
        inning = simulate(f"B B S {terminal}")
        assert inning.count == Count()

    def test_count_reset_prevents_carryover_walk(self) -> None:
        # Three balls, then the batter grounds out; the next batter's first ball
        # must not complete a walk.
        inning = simulate("B B B GO B")
        assert inning.count == Count(balls=1, strikes=0)
        assert inning.bases_occupied() == (False, False, False)

    def test_count_reset_prevents_carryover_strikeout(self) -> None:
        inning = simulate("S S 1B S")
        assert inning.outs == 0
        assert inning.count == Count(balls=0, strikes=1)

    def test_four_pitch_walk_matches_bb_code(self) -> None:
        for prefix in ["", "1B", "1B 1B", "1B 1B 1B", "2B", "3B", "1B 2B"]:
            via_pitches = simulate(f"{prefix} B B B B")
            via_code = simulate(f"{prefix} BB")
            assert via_pitches.bases_occupied() == via_code.bases_occupied()
            assert via_pitches.runs == via_code.runs


# --- Walks and forced runners ----------------------------------------------


@pytest.mark.parametrize(
    ("before", "after", "runs"),
    [
        ((False, False, False), (True, False, False), 0),
        ((True, False, False), (True, True, False), 0),
        ((False, True, False), (True, True, False), 0),  # runner on 2nd not forced
        ((False, False, True), (True, False, True), 0),  # runner on 3rd not forced
        ((True, True, False), (True, True, True), 0),
        ((True, False, True), (True, True, True), 0),
        ((False, True, True), (True, True, True), 0),  # nobody forced home
        ((True, True, True), (True, True, True), 1),
    ],
)
def test_walk_forces_only_when_necessary(
    before: tuple[bool, bool, bool], after: tuple[bool, bool, bool], runs: int
) -> None:
    assert Bases(before).force_batter_to_first() == (Bases(after), runs)


def test_walk_with_runners_on_second_and_third_via_simulation() -> None:
    # 1B then 2B: runner goes 1st -> 3rd, batter to 2nd.
    inning = simulate("1B 2B BB")
    assert inning.bases_occupied() == (True, True, True)
    assert inning.runs == 0


# --- Hits ------------------------------------------------------------------


@pytest.mark.parametrize(
    ("sequence", "bases", "runs"),
    [
        ("1B", (True, False, False), 0),
        ("2B", (False, True, False), 0),
        ("3B", (False, False, True), 0),
        ("HR", (False, False, False), 1),
        ("1B 2B", (False, True, True), 0),
        ("1B 3B", (False, False, True), 1),
        ("2B 1B", (True, False, True), 0),
        ("2B 2B", (False, True, False), 1),
        ("3B 1B", (True, False, False), 1),
        ("1B 1B 1B HR", (False, False, False), 4),  # grand slam
        ("1B 1B 1B 3B", (False, False, True), 3),
        ("1B 1B 1B 2B", (False, True, True), 2),
    ],
)
def test_hits_advance_everyone_by_the_hit_value(
    sequence: str, bases: tuple[bool, bool, bool], runs: int
) -> None:
    inning = simulate(sequence)
    assert inning.bases_occupied() == bases
    assert inning.runs == runs


@pytest.mark.parametrize("occupied", list(product([False, True], repeat=3)))
def test_home_run_always_scores_everyone(occupied: tuple[bool, bool, bool]) -> None:
    new_bases, runs = Bases(occupied).advance_all(4)
    assert new_bases == Bases.empty()
    assert runs == 1 + sum(occupied)


def test_runs_accumulate_across_plate_appearances() -> None:
    assert simulate("HR HR 1B HR").runs == 4  # 1 + 1 + (runner + batter)


# --- Outs and the end of the inning ----------------------------------------


@pytest.mark.parametrize("out", ["K", "GO", "FO"])
def test_outs_leave_runners_in_place(out: str) -> None:
    inning = simulate(f"1B 2B {out}")
    assert inning.bases_occupied() == (False, True, True)
    assert inning.outs == 1


def test_mixed_outs_end_the_inning() -> None:
    inning = simulate("GO FO S S S")
    assert inning.over is True
    assert inning.outs == 3


def test_runs_before_the_third_out_count() -> None:
    inning = simulate("HR 1B K GO FO")
    assert inning.runs == 1
    assert inning.over is True
    assert inning.bases_occupied() == (True, False, False)


@pytest.mark.parametrize("late_event", ["B", "S", "F", "1B", "HR", "BB", "K", "GO", "FO"])
def test_any_event_after_third_out_raises(late_event: str) -> None:
    with pytest.raises(InningOverError):
        simulate(f"K K K {late_event}")


def test_rejected_event_does_not_change_state() -> None:
    inning = simulate("HR K K K")
    with pytest.raises(InningOverError):
        inning.process("HR")
    assert (inning.runs, inning.outs, inning.over) == (1, 3, True)


def test_inning_not_over_with_two_outs() -> None:
    inning = simulate("K K")
    assert inning.over is False


# --- Input handling --------------------------------------------------------


def test_empty_sequence() -> None:
    for sequence in ("", "   ", []):
        inning = simulate(sequence)
        assert (inning.runs, inning.outs, inning.over) == (0, 0, False)
        assert inning.bases_occupied() == (False, False, False)


def test_list_input_matches_string_input() -> None:
    codes = ["1B", "1B", "HR"]
    assert simulate(codes).runs == simulate(" ".join(codes)).runs


def test_event_enum_input() -> None:
    inning = simulate([Event.SINGLE, Event.HOME_RUN])
    assert inning.runs == 2


def test_generator_input() -> None:
    assert simulate(code for code in ["K", "K", "K"]).over is True


def test_irregular_whitespace_and_case() -> None:
    inning = simulate("  1b\t1B \n hr ")
    assert inning.runs == 3


@pytest.mark.parametrize("bad", ["X", "4B", "SO", "1", "BBB"])
def test_unknown_code_raises(bad: str) -> None:
    with pytest.raises(InvalidEventError, match="unknown event code"):
        simulate(f"1B {bad}")


def test_invalid_event_error_is_a_value_error_and_simulation_error() -> None:
    with pytest.raises(ValueError):
        simulate("X")
    with pytest.raises(SimulationError):
        simulate("X")


def test_incremental_processing() -> None:
    inning = HalfInning()
    for code in "B B B B".split():
        inning.process(code)
    assert inning.bases_occupied() == (True, False, False)


# --- Extensibility ---------------------------------------------------------


def test_every_event_has_an_action() -> None:
    assert set(EVENT_ACTIONS) == set(Event)


def test_custom_rules() -> None:
    youth = Rules(balls_for_walk=3, strikes_for_strikeout=2, outs_per_inning=1)
    assert simulate("B B B", youth).bases_occupied() == (True, False, False)
    assert simulate("F F", youth).outs == 0  # foul still can't be strike two here
    assert simulate("S S", youth).over is True


@pytest.mark.parametrize("field", ["balls_for_walk", "strikes_for_strikeout", "outs_per_inning"])
def test_invalid_rules_rejected(field: str) -> None:
    with pytest.raises(ValueError):
        Rules(**{field: 0})


def test_custom_outcome_can_be_plugged_in() -> None:
    @dataclass(frozen=True)
    class SacrificeFly:
        """Batter out; a runner on third tags up and scores."""

        def resolve(self, bases: Bases) -> PlayResult:
            first, second, third = bases.occupied
            return PlayResult(Bases((first, second, False)), runs_scored=int(third), outs_recorded=1)

    actions = {**EVENT_ACTIONS, Event.FLYOUT: SacrificeFly()}
    inning = HalfInning(actions=actions)
    inning.process_all("3B FO".split())
    assert (inning.runs, inning.outs) == (1, 1)
    assert inning.bases_occupied() == (False, False, False)


def test_bases_reject_wrong_length() -> None:
    with pytest.raises(ValueError):
        Bases((True, False))


def test_hit_must_advance_at_least_one_base() -> None:
    with pytest.raises(ValueError):
        Bases.empty().advance_all(0)


def test_count_is_immutable() -> None:
    count = Count()
    assert count.after(Pitch.BALL, Rules()) == Count(balls=1)
    assert count == Count()
