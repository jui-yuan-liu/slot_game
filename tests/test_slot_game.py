"""Regression tests for payout and evaluation."""

from __future__ import annotations

import unittest

from slot_game.config import DEFAULT_RULES
from slot_game.evaluate import Evaluator
from slot_game.models import ReelSet, Screen
from slot_game.payout import PayoutEngine
from slot_game.solutions import SOLUTION, SOLUTION_REELS


class PayoutTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = PayoutEngine()

    def test_bottom_left_symbol_4_pays_500(self) -> None:
        # 4 0 0
        # 4 4 0
        # 4 4 0  -> only bottom-left 2x2 of 4s
        screen = Screen(((4, 4, 4), (0, 4, 4), (0, 0, 0)))
        self.assertEqual(self.engine.payout_units(screen), DEFAULT_RULES.units_of(4))
        self.assertEqual(self.engine.amount(screen), 500.0)

    def test_two_symbol_0_squares_stack(self) -> None:
        # 4 0 0
        # 4 0 0
        # 4 0 0  -> top-right and bottom-right 2x2 of 0s
        screen = Screen(((4, 4, 4), (0, 0, 0), (0, 0, 0)))
        self.assertEqual(self.engine.payout_units(screen), 2 * DEFAULT_RULES.units_of(0))
        self.assertEqual(self.engine.amount(screen), 50.0)


class EvaluatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.evaluator = Evaluator()

    def test_solution_meets_spec(self) -> None:
        stats = self.evaluator.evaluate(SOLUTION)
        self.assertTrue(stats.valid())
        self.assertTrue(stats.exact_rtp)
        self.assertEqual(stats.n_combinations, 1000)
        self.assertEqual(stats.n_wins, 570)
        self.assertEqual(stats.payout_units, 19 * 1000)
        self.assertEqual(stats.rtp, 0.95)
        self.assertEqual(stats.win_rate, 0.57)

    def test_fast_matches_brute(self) -> None:
        stats = self.evaluator.evaluate(SOLUTION)
        brute = self.evaluator.evaluate_brute(SOLUTION)
        self.assertEqual(stats, brute)

    def test_rejects_bad_symbol(self) -> None:
        with self.assertRaises(ValueError):
            ReelSet.from_lists([[0, 0, 0], [1, 1, 1], [5, 5, 5]])

    def test_list_facade_matches_package_api(self) -> None:
        from slot_game import evaluate

        stats = evaluate(SOLUTION_REELS)
        self.assertTrue(stats.valid())


if __name__ == "__main__":
    unittest.main()
