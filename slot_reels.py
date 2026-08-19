#!/usr/bin/env python3
"""CLI entry point. Implementation lives in the `slot_game` package."""

from slot_game.cli import main
from slot_game.evaluate import evaluate, evaluate_brute
from slot_game.models import Stats
from slot_game.search import search
from slot_game.solutions import SOLUTION_REELS

__all__ = ["SOLUTION_REELS", "Stats", "evaluate", "evaluate_brute", "main", "search"]


if __name__ == "__main__":
    raise SystemExit(main())
