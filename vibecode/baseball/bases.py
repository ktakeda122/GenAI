"""Immutable model of the baserunners."""

from __future__ import annotations

from dataclasses import dataclass

NUM_BASES = 3


@dataclass(frozen=True, slots=True)
class Bases:
    """Which bases are occupied, ordered (first, second, third)."""

    occupied: tuple[bool, ...] = (False,) * NUM_BASES

    def __post_init__(self) -> None:
        if len(self.occupied) != NUM_BASES:
            raise ValueError(f"expected {NUM_BASES} bases, got {len(self.occupied)}")

    @classmethod
    def empty(cls) -> Bases:
        return cls()

    def advance_all(self, num_bases: int) -> tuple[Bases, int]:
        """Move the batter and every runner forward ``num_bases`` bases.

        Returns the new bases and the number of runs scored. Position 0 is
        home plate (the batter); a runner whose new position is past the last
        base scores.
        """
        if num_bases < 1:
            raise ValueError("a hit must advance at least one base")

        runner_positions = [0] + [i + 1 for i, taken in enumerate(self.occupied) if taken]
        new_occupied = [False] * NUM_BASES
        runs = 0
        for position in runner_positions:
            destination = position + num_bases
            if destination > NUM_BASES:
                runs += 1
            else:
                new_occupied[destination - 1] = True
        return Bases(tuple(new_occupied)), runs

    def force_batter_to_first(self) -> tuple[Bases, int]:
        """Award the batter first base, forcing runners ahead only as needed.

        Every runner in the unbroken chain of occupied bases starting at first
        moves up one, so the net effect is that the first empty base gets
        filled. If there is no empty base, the runner on third is forced home.
        """
        for index, taken in enumerate(self.occupied):
            if not taken:
                new_occupied = list(self.occupied)
                new_occupied[index] = True
                return Bases(tuple(new_occupied)), 0
        return self, 1
