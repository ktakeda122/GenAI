"""The acceptance cases from the specification."""

from baseball import simulate


def test_three_strikeouts_end_the_inning() -> None:
    inning = simulate("K K K")
    assert inning.runs == 0
    assert inning.outs == 3
    assert inning.over is True


def test_four_singles_score_one_and_load_the_bases() -> None:
    inning = simulate("1B 1B 1B 1B")
    assert inning.runs == 1
    assert inning.outs == 0
    assert inning.bases_occupied() == (True, True, True)


def test_home_run_clears_the_bases() -> None:
    inning = simulate("1B 1B HR")
    assert inning.runs == 3
    assert inning.bases_occupied() == (False, False, False)


def test_bases_loaded_walk_forces_in_a_run() -> None:
    inning = simulate("1B 1B 1B BB")
    assert inning.runs == 1
    assert inning.bases_occupied() == (True, True, True)


def test_four_balls_is_a_walk() -> None:
    inning = simulate("B B B S S B")
    assert inning.runs == 0
    assert inning.outs == 0
    assert inning.bases_occupied() == (True, False, False)


def test_fouls_with_two_strikes_do_not_end_the_at_bat() -> None:
    inning = simulate("S S F F S")
    assert inning.outs == 1
    assert inning.over is False


def test_steal_moves_runner_from_first_to_second() -> None:
    assert simulate("1B SB").bases_occupied() == (False, True, False)


def test_steal_with_empty_bases_does_nothing() -> None:
    assert simulate("SB").bases_occupied() == (False, False, False)


def test_steal_is_blocked_when_second_is_occupied() -> None:
    assert simulate("1B 1B SB").bases_occupied() == (True, True, False)


def test_steal_does_not_end_plate_appearance_or_change_count() -> None:
    inning = simulate("1B SB S S S")
    assert inning.outs == 1
    assert inning.runs == 0
    assert inning.bases_occupied() == (False, True, False)
    assert (simulate("B S SB").count.balls, simulate("B S SB").count.strikes) == (1, 1)
