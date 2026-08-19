"""Exact RTP / win-rate evaluation over every stop combination."""

from __future__ import annotations

from slot_game.config import DEFAULT_RULES, GameRules
from slot_game.models import ReelSet, Screen, Stats
from slot_game.payout import FULL_SCREEN, LEFT_2X2, PayoutEngine, RIGHT_2X2, WinningPattern


def _left_pair_screen(col1, col2) -> Screen:
    """2x2 patterns on columns 0–1 ignore column 2."""
    return Screen((col1, col2, col2))


def _right_pair_screen(col2, col3) -> Screen:
    """2x2 patterns on columns 1–2 ignore column 0."""
    return Screen((col2, col2, col3))


class Evaluator:
    def __init__(self, rules: GameRules = DEFAULT_RULES, engine: PayoutEngine | None = None) -> None:
        self.rules = rules
        self.engine = engine or PayoutEngine(rules)

    def evaluate(self, reel_set: ReelSet) -> Stats:
        """O(L1*L2 + L2*L3) closed form; equivalent to brute force."""
        reel_set = reel_set.validated(self.rules)
        w1, w2, w3 = (strip.windows() for strip in reel_set.strips)
        l1, l2, l3 = len(w1), len(w2), len(w3)
        n = l1 * l2 * l3

        left_pay = [[0] * l2 for _ in range(l1)]
        left_hit = [[False] * l2 for _ in range(l1)]
        for i, col1 in enumerate(w1):
            for j, col2 in enumerate(w2):
                screen = _left_pair_screen(col1, col2)
                pay = sum(self._pattern_units(pattern, screen) for pattern in LEFT_2X2)
                left_pay[i][j] = pay
                left_hit[i][j] = pay > 0

        right_pay = [[0] * l3 for _ in range(l2)]
        right_hit = [[False] * l3 for _ in range(l2)]
        for j, col2 in enumerate(w2):
            for k, col3 in enumerate(w3):
                screen = _right_pair_screen(col2, col3)
                pay = sum(self._pattern_units(pattern, screen) for pattern in RIGHT_2X2)
                right_pay[j][k] = pay
                right_hit[j][k] = pay > 0

        payout_units = 0
        for i in range(l1):
            for j in range(l2):
                payout_units += left_pay[i][j] * l3
        for j in range(l2):
            for k in range(l3):
                payout_units += right_pay[j][k] * l1

        solid = [[0] * self.rules.n_symbols for _ in range(3)]
        for idx, windows in enumerate((w1, w2, w3)):
            for top, mid, bot in windows:
                if top == mid == bot:
                    solid[idx][top] += 1
        for symbol in self.rules.symbol_ids:
            payout_units += (
                FULL_SCREEN.extra_multiplier
                * self.rules.units_of(symbol)
                * solid[0][symbol]
                * solid[1][symbol]
                * solid[2][symbol]
            )

        n_left = [sum(1 for i in range(l1) if left_hit[i][j]) for j in range(l2)]
        n_right = [sum(1 for k in range(l3) if right_hit[j][k]) for j in range(l2)]
        n_wins = 0
        for j in range(l2):
            n_wins += n_left[j] * l3 + (l1 - n_left[j]) * n_right[j]

        return self._to_stats(payout_units, n_wins, n)

    def evaluate_brute(self, reel_set: ReelSet) -> Stats:
        """Enumerate every stop. Used to cross-check evaluate()."""
        reel_set = reel_set.validated(self.rules)
        payout_units = n_wins = n = 0
        for screen in reel_set.iter_screens():
            n += 1
            pay = self.engine.payout_units(screen)
            payout_units += pay
            if pay:
                n_wins += 1
        return self._to_stats(payout_units, n_wins, n)

    def _pattern_units(self, pattern: WinningPattern, screen: Screen) -> int:
        symbol = pattern.matched_symbol(screen)
        if symbol is None:
            return 0
        return pattern.extra_multiplier * self.rules.units_of(symbol)

    def _to_stats(self, payout_units: int, n_wins: int, n: int) -> Stats:
        rtp = payout_units / (self.rules.unit_scale * n)
        return Stats(
            rtp=rtp,
            win_rate=n_wins / n,
            n_combinations=n,
            expected_return=rtp * self.rules.bet,
            payout_units=payout_units,
            n_wins=n_wins,
            exact_rtp=payout_units == self.rules.target_rtp_units * n,
            min_win_rate=self.rules.min_win_rate,
        )


_DEFAULT_EVALUATOR = Evaluator()


def evaluate(reels: list[list[int]]) -> Stats:
    return _DEFAULT_EVALUATOR.evaluate(ReelSet.from_lists(reels))


def evaluate_brute(reels: list[list[int]]) -> Stats:
    return _DEFAULT_EVALUATOR.evaluate_brute(ReelSet.from_lists(reels))
