"""Pytest suite for the half-inning simulator.

Covers the six shared acceptance cases from CLAUDE.md plus edge cases: the count
(fouls and resets), walk forcing from every base state, hits advancing runners,
outs leaving runners put, error handling, and input formats.

The module file is Half_inning.py. Although the backlog spec wrote the import as
``from half_inning import ...``, CPython performs a case-sensitivity check on
import even on case-insensitive filesystems, so the module must be imported with
its real filename case.
"""

import pytest

from Half_inning import simulate, InningOver, HalfInning, parse_event


def snapshot(inning: HalfInning):
    """The public, observable state of an inning."""
    return (inning.runs, inning.outs, inning.over, inning.bases_occupied())


# -- 1. The six shared acceptance cases from CLAUDE.md -----------------------

@pytest.mark.parametrize(
    "sequence, runs, outs, over, bases",
    [
        ("K K K",        0, 3, True,  (False, False, False)),
        ("1B 1B 1B 1B",  1, 0, False, (True, True, True)),
        ("1B 1B HR",     3, 0, False, (False, False, False)),
        ("1B 1B 1B BB",  1, 0, False, (True, True, True)),
        ("B B B S S B",  0, 0, False, (True, False, False)),
        ("S S F F S",    0, 1, False, (False, False, False)),
    ],
)
def test_shared_acceptance_cases(sequence, runs, outs, over, bases):
    inning = simulate(sequence)
    assert snapshot(inning) == (runs, outs, over, bases)


# -- 2. The count ------------------------------------------------------------

@pytest.mark.parametrize("sequence", ["S S F", "S S F F F"])
def test_foul_never_makes_the_third_strike(sequence):
    inning = simulate(sequence)
    assert inning.strikes == 2
    assert inning.outs == 0
    assert inning.over is False


def test_foul_below_two_strikes_is_a_strike():
    # two fouls take the count to two strikes, so the next strike is a strikeout
    inning = simulate("F F S")
    assert inning.outs == 1


@pytest.mark.parametrize(
    "sequence",
    ["B S 1B", "B S 2B", "B S 3B", "B S HR", "B S GO", "B S FO", "S S S", "B B B B"],
)
def test_count_resets_after_every_ending(sequence):
    # whatever balls/strikes accrued, the plate appearance ending clears them
    inning = simulate(sequence)
    assert inning.balls == 0
    assert inning.strikes == 0


# -- 3. Walks force runners in from every relevant base state ----------------

@pytest.mark.parametrize(
    "sequence, runs, bases",
    [
        ("BB",            0, (True, False, False)),   # empty
        ("1B BB",         0, (True, True, False)),    # first only
        ("1B 1B BB",      0, (True, True, True)),     # first + second
        ("1B 1B 1B BB",   1, (True, True, True)),     # loaded: forces in one run
    ],
)
def test_walk_forces_runners(sequence, runs, bases):
    inning = simulate(sequence)
    assert inning.runs == runs
    assert inning.bases_occupied() == bases


# -- 4. Hits advance every runner (and the batter) by the hit's bases --------

@pytest.mark.parametrize(
    "sequence, runs, bases",
    [
        # singles
        ("1B 1B",       0, (True, True, False)),
        ("1B 1B 1B",    0, (True, True, True)),
        # doubles
        ("2B",          0, (False, True, False)),
        ("1B 2B",       0, (False, True, True)),    # runner first->third, batter->second
        ("2B 2B",       1, (False, True, False)),   # runner on second scores
        # triples
        ("3B",          0, (False, False, True)),
        ("1B 3B",       1, (False, False, True)),   # runner on first scores
        # home runs
        ("HR",          1, (False, False, False)),
        ("1B 1B 1B HR", 4, (False, False, False)),  # grand slam
    ],
)
def test_hits_advance_runners(sequence, runs, bases):
    inning = simulate(sequence)
    assert inning.runs == runs
    assert inning.bases_occupied() == bases


# -- 5. Outs leave runners where they are ------------------------------------

@pytest.mark.parametrize(
    "sequence, outs, bases",
    [
        ("1B GO",     1, (True, False, False)),
        ("1B FO",     1, (True, False, False)),
        ("1B 2B GO",  1, (False, True, True)),   # no advancement on the out
    ],
)
def test_outs_do_not_advance_runners(sequence, outs, bases):
    inning = simulate(sequence)
    assert inning.outs == outs
    assert inning.runs == 0
    assert inning.bases_occupied() == bases


# -- 6. Errors ---------------------------------------------------------------

def test_unknown_event_code_raises_value_error():
    with pytest.raises(ValueError):
        simulate("ZZ")


def test_event_after_third_out_raises_and_leaves_state_unchanged():
    inning = simulate("K K K")
    assert inning.over is True
    before = snapshot(inning)
    with pytest.raises(InningOver):
        inning.play(parse_event("1B"))
    assert snapshot(inning) == before


# -- 7. Input formats --------------------------------------------------------

def test_string_and_list_inputs_are_equivalent():
    from_string = simulate("1B 2B")
    from_list = simulate(["1B", "2B"])
    assert snapshot(from_string) == snapshot(from_list)


@pytest.mark.parametrize("empty", ["", []])
def test_empty_input_is_a_fresh_scoreless_inning(empty):
    inning = simulate(empty)
    assert snapshot(inning) == (0, 0, False, (False, False, False))
