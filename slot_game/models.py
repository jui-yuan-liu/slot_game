"""Domain objects: strips, screens, and evaluation results."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator, Sequence

from slot_game.config import DEFAULT_RULES, GameRules

Column = tuple[int, int, int]


@dataclass(frozen=True)
class ReelStrip:
    """One circular reel. A stop `i` shows symbols i, i+1, i+2 (wrapping)."""

    symbols: tuple[int, ...]

    def __post_init__(self) -> None:
        if len(self.symbols) < 1:
            raise ValueError("reel strip cannot be empty")

    def __len__(self) -> int:
        return len(self.symbols)

    def window(self, stop: int) -> Column:
        n = len(self.symbols)
        i = stop % n
        return (
            self.symbols[i],
            self.symbols[(i + 1) % n],
            self.symbols[(i + 2) % n],
        )

    def windows(self) -> tuple[Column, ...]:
        return tuple(self.window(i) for i in range(len(self)))


@dataclass(frozen=True)
class ReelSet:
    """Three independent circular reels that form the 3x3 screen."""

    strips: tuple[ReelStrip, ReelStrip, ReelStrip]

    @classmethod
    def from_lists(cls, reels: Sequence[Sequence[int]], rules: GameRules = DEFAULT_RULES) -> ReelSet:
        if len(reels) != rules.n_reels:
            raise ValueError(f"need exactly {rules.n_reels} reels")
        strips = tuple(ReelStrip(tuple(reel)) for reel in reels)
        return cls((strips[0], strips[1], strips[2])).validated(rules)

    def validated(self, rules: GameRules = DEFAULT_RULES) -> ReelSet:
        if len(self.strips) != rules.n_reels:
            raise ValueError(f"need exactly {rules.n_reels} reels")
        for strip in self.strips:
            if len(strip) < rules.min_reel_length:
                raise ValueError(f"each reel must have length >= {rules.min_reel_length}")
            if any(s not in rules.symbol_ids for s in strip.symbols):
                raise ValueError(f"symbols must be in {set(rules.symbol_ids)}")
        return self

    def to_lists(self) -> list[list[int]]:
        return [list(strip.symbols) for strip in self.strips]

    def __len__(self) -> int:
        return len(self.strips)

    @property
    def lengths(self) -> tuple[int, ...]:
        return tuple(len(strip) for strip in self.strips)

    @property
    def n_combinations(self) -> int:
        n = 1
        for length in self.lengths:
            n *= length
        return n

    def screen_at(self, stops: Sequence[int]) -> Screen:
        if len(stops) != len(self.strips):
            raise ValueError("stop count must match reel count")
        col1, col2, col3 = (strip.window(stop) for strip, stop in zip(self.strips, stops))
        return Screen((col1, col2, col3))

    def iter_screens(self) -> Iterator[Screen]:
        w1, w2, w3 = (strip.windows() for strip in self.strips)
        for col1 in w1:
            for col2 in w2:
                for col3 in w3:
                    yield Screen((col1, col2, col3))


@dataclass(frozen=True)
class Screen:
    """Visible 3x3 grid, stored as three columns of (top, middle, bottom)."""

    columns: tuple[Column, Column, Column]

    def symbol_at(self, row: int, col: int) -> int:
        return self.columns[col][row]

    def rows(self) -> tuple[tuple[int, int, int], ...]:
        return tuple(tuple(self.symbol_at(row, col) for col in range(3)) for row in range(3))

    def render(self) -> str:
        return "\n".join("  " + " ".join(str(v) for v in row) for row in self.rows())


@dataclass(frozen=True)
class Stats:
    rtp: float
    win_rate: float
    n_combinations: int
    expected_return: float
    payout_units: int
    n_wins: int
    exact_rtp: bool
    min_win_rate: float = DEFAULT_RULES.min_win_rate

    def valid(self) -> bool:
        return self.exact_rtp and self.win_rate >= self.min_win_rate

    # Backward-compatible alias used by the original script.
    @property
    def payout_20(self) -> int:
        return self.payout_units


@dataclass(frozen=True)
class SpinResult:
    stops: tuple[int, ...]
    screen: Screen
    payout_units: int
    payout_amount: float
