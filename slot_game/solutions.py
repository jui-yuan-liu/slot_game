"""Known valid reel configurations."""

from __future__ import annotations

from slot_game.models import ReelSet

# RTP = 0.95 exactly, win rate = 57%.
SOLUTION_REELS: list[list[int]] = [
    [4, 4, 4, 0, 2, 2, 1, 1, 4, 4],
    [4, 4, 3, 0, 0, 0, 0, 0, 0, 4],
    [1, 0, 0, 0, 2, 0, 0, 0, 0, 0],
]

SOLUTION = ReelSet.from_lists(SOLUTION_REELS)
