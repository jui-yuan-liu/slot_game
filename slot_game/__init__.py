"""3x3 slot reel configuration: domain model, exact evaluation, and search."""

from slot_game.config import DEFAULT_RULES, GameRules
from slot_game.evaluate import Evaluator, evaluate, evaluate_brute
from slot_game.models import ReelSet, Screen, SpinResult, Stats
from slot_game.payout import PayoutEngine
from slot_game.search import ReelOptimizer, SearchConfig, search
from slot_game.solutions import SOLUTION, SOLUTION_REELS

__all__ = [
    "DEFAULT_RULES",
    "Evaluator",
    "GameRules",
    "PayoutEngine",
    "ReelOptimizer",
    "ReelSet",
    "SOLUTION",
    "SOLUTION_REELS",
    "Screen",
    "SearchConfig",
    "SpinResult",
    "Stats",
    "evaluate",
    "evaluate_brute",
    "search",
]
