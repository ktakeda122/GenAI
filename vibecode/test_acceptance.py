"""Shared acceptance tests for the three half-inning implementations.

Copy this file into EACH implementation's folder (byhand, vibecode, together)
and run it there:

    uv run --with pytest pytest test_acceptance.py -q

It imports `simulate` from whichever implementation lives in that folder
(half_inning.py for byhand / together, the `baseball` package for vibecode) and
checks that all three satisfy the SAME observable contract:

    simulate(sequence) -> object with .runs, .outs, .over, .bases_occupied()

Only behaviour that every version shares is tested here, so this is a fair
cross-version baseline. Version-specific details (exception classes, extra
features) belong in each version's own test file, not here.

Note: together's module file must be named half_inning.py (lowercase) for the
first import to succeed, because CPython enforces the recorded case even on a
case-insensitive filesystem.
"""

import pytest

try:
    from half_inning import simulate            # byhand / together
except ModuleNotFoundError:
    from baseball import simulate                # vibecode


def _state(inning):
    """The shared, observable state of a finished half-inning."""
    return (inning.runs, inning.outs, inning.over, inning.bases_occupied())


# sequence -> (runs, outs, over, bases_occupied())
SHARED_CASES = [
    # --- the six required acceptance cases from CLAUDE.md ---------------
    ("K K K",        (0, 3, True,  (False, False, False))),
    ("1B 1B 1B 1B",  (1, 0, False, (True,  True,  True))),
    ("1B 1B HR",     (3, 0, False, (False, False, False))),
    ("1B 1B 1B BB",  (1, 0, False, (True,  True,  True))),
    ("B B B S S B",  (0, 0, False, (True,  False, False))),
    ("S S F F S",    (0, 1, False, (False, False, False))),
    # --- extra behaviour every version should share -------------------
    ("",             (0, 0, False, (False, False, False))),   # empty input
    ("HR",           (1, 0, False, (False, False, False))),   # solo homer
    ("BB",           (0, 0, False, (True,  False, False))),   # walk, empty bases
    ("1B BB",        (0, 0, False, (True,  True,  False))),   # walk forces to 2nd
    ("1B 1B 1B HR",  (4, 0, False, (False, False, False))),   # grand slam
    ("2B",           (0, 0, False, (False, True,  False))),   # double
    ("3B",           (0, 0, False, (False, False, True))),    # triple
    ("2B 2B",        (1, 0, False, (False, True,  False))),   # runner scores from 2nd
    ("1B GO",        (0, 1, False, (True,  False, False))),   # out leaves runner on 1st
    ("1B FO",        (0, 1, False, (True,  False, False))),   # flyout leaves runner on 1st
    ("F F S",        (0, 1, False, (False, False, False))),   # fouls below 2 strikes are strikes
    ("S S F",        (0, 0, False, (False, False, False))),   # foul at 2 strikes is not the 3rd
    ("S S 1B S S S", (0, 1, False, (True,  False, False))),   # count resets after the single
]


@pytest.mark.parametrize("sequence,expected", SHARED_CASES)
def test_shared_behaviour(sequence, expected):
    assert _state(simulate(sequence)) == expected


def test_string_and_list_are_equivalent():
    assert _state(simulate("1B 2B HR")) == _state(simulate(["1B", "2B", "HR"]))


def test_unknown_code_is_an_error():
    # Every version raises ValueError (vibecode's InvalidEventError subclasses it).
    with pytest.raises(ValueError):
        simulate("ZZ")
