"""Command-line interface. No game rules live here."""

from __future__ import annotations

import argparse
import random
import sys

from slot_game.config import DEFAULT_RULES, GameRules
from slot_game.evaluate import Evaluator
from slot_game.models import ReelSet, SpinResult, Stats
from slot_game.payout import PayoutEngine
from slot_game.search import ReelOptimizer, SearchConfig
from slot_game.solutions import SOLUTION, SOLUTION_REELS


def spin(reel_set: ReelSet, rng: random.Random, rules: GameRules = DEFAULT_RULES) -> SpinResult:
    stops = tuple(rng.randrange(len(strip)) for strip in reel_set.strips)
    screen = reel_set.screen_at(stops)
    units = PayoutEngine(rules).payout_units(screen)
    return SpinResult(
        stops=stops,
        screen=screen,
        payout_units=units,
        payout_amount=rules.amount_from_units(units),
    )


def format_report(reel_set: ReelSet, stats: Stats, rules: GameRules = DEFAULT_RULES) -> str:
    lines = ["Reel 配置（3 條循環滾筒，每欄一條）："]
    for i, strip in enumerate(reel_set.strips, 1):
        lines.append(f"  reel {i} (len={len(strip)}): {list(strip.symbols)}")
    lines.extend(
        [
            "",
            f"停輪組合數     : {stats.n_combinations}",
            f"下注金額       : {rules.bet}",
            f"期望返還       : {stats.expected_return:.6f}",
            f"RTP            : {stats.rtp:.12f}   (恰好 {rules.target_rtp} = {stats.exact_rtp})",
            f"勝率           : {stats.win_rate:.12f}   ({stats.n_wins}/{stats.n_combinations}, >={rules.min_win_rate} = {stats.win_rate >= rules.min_win_rate})",
            f"符合題目       : {stats.valid()}",
        ]
    )
    return "\n".join(lines)


def format_spin(result: SpinResult, rules: GameRules = DEFAULT_RULES) -> str:
    return (
        f"stops = {list(result.stops)}\n"
        f"{result.screen.render()}\n"
        f"payout = {result.payout_amount:.2f}  (bet={rules.bet})"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="產生並驗證 3x3 slot reel 配置")
    parser.add_argument("--search", action="store_true", help="重新搜尋一組解，而不是使用內建解")
    parser.add_argument("--seed", type=int, default=19, help="搜尋 / 示範旋轉的亂數種子")
    parser.add_argument("--demo", type=int, default=0, metavar="N", help="額外示範 N 次隨機旋轉")
    return parser


def resolve_reels(search: bool, seed: int, evaluator: Evaluator) -> tuple[ReelSet, Stats]:
    if search:
        return ReelOptimizer(config=SearchConfig(seed=seed)).search()

    stats = evaluator.evaluate(SOLUTION)
    if stats.valid():
        return SOLUTION, stats
    return ReelOptimizer(config=SearchConfig(seed=seed)).search()


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    rules = DEFAULT_RULES
    evaluator = Evaluator(rules)

    reel_set, stats = resolve_reels(search=args.search, seed=args.seed, evaluator=evaluator)
    brute = evaluator.evaluate_brute(reel_set)
    if brute != stats:
        print(f"內部驗證失敗：fast={stats} brute={brute}", file=sys.stderr)
        return 1

    print(format_report(reel_set, stats, rules))

    if args.demo:
        print()
        rng = random.Random(args.seed)
        for i in range(args.demo):
            print(f"--- spin {i + 1} ---")
            print(format_spin(spin(reel_set, rng, rules), rules))
    return 0


# Re-export for the thin slot_reels.py shim.
__all__ = ["main", "spin", "format_report", "SOLUTION_REELS"]
