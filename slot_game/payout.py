"""Winning patterns and per-screen payout.

Patterns are data. Adding a new shape should not require rewriting the evaluator.
"""

from __future__ import annotations

from dataclasses import dataclass

from slot_game.config import DEFAULT_RULES, GameRules
from slot_game.models import Screen


@dataclass(frozen=True)
class WinningPattern:
    name: str
    cells: tuple[tuple[int, int], ...]  # (row, col), row 0 is the top
    extra_multiplier: int = 1

    def matched_symbol(self, screen: Screen) -> int | None:
        first = screen.symbol_at(*self.cells[0])
        for row, col in self.cells[1:]:
            if screen.symbol_at(row, col) != first:
                return None
        return first


# 4.1–4.4 pay bet * multiplier; 4.5 pays bet * multiplier * 5.
PATTERNS: tuple[WinningPattern, ...] = (
    WinningPattern("top_left", ((0, 0), (0, 1), (1, 0), (1, 1))),
    WinningPattern("top_right", ((0, 1), (0, 2), (1, 1), (1, 2))),
    WinningPattern("bottom_left", ((1, 0), (1, 1), (2, 0), (2, 1))),
    WinningPattern("bottom_right", ((1, 1), (1, 2), (2, 1), (2, 2))),
    WinningPattern(
        "full_screen",
        tuple((row, col) for row in range(3) for col in range(3)),
        extra_multiplier=5,
    ),
)

LEFT_2X2 = (PATTERNS[0], PATTERNS[2])   # depend only on reels 0 and 1
RIGHT_2X2 = (PATTERNS[1], PATTERNS[3])  # depend only on reels 1 and 2
FULL_SCREEN = PATTERNS[4]


class PayoutEngine:
    """Scores one screen. Matching patterns stack."""

    def __init__(self, rules: GameRules = DEFAULT_RULES) -> None:
        self.rules = rules

    def payout_units(self, screen: Screen) -> int:
        total = 0
        for pattern in PATTERNS:
            symbol = pattern.matched_symbol(screen)
            if symbol is None:
                continue
            total += pattern.extra_multiplier * self.rules.units_of(symbol)
        return total

    def amount(self, screen: Screen) -> float:
        return self.rules.amount_from_units(self.payout_units(screen))
