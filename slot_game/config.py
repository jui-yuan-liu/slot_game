"""Game rules and numeric constants.

Changing paytable or constraints should happen here, not in evaluation or search.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GameRules:
    n_reels: int = 3
    visible_rows: int = 3
    bet: int = 100
    min_win_rate: float = 0.55
    min_reel_length: int = 3
    # Integer scale so RTP 0.95 = 19/20 can be checked exactly.
    unit_scale: int = 20
    target_rtp_units: int = 19
    # symbol id -> multiplier, and the same values in 1/20 units
    multipliers: tuple[float, ...] = (0.25, 0.55, 1.0, 3.0, 5.0)
    multiplier_units: tuple[int, ...] = (5, 11, 20, 60, 100)

    @property
    def n_symbols(self) -> int:
        return len(self.multipliers)

    @property
    def symbol_ids(self) -> range:
        return range(self.n_symbols)

    @property
    def target_rtp(self) -> float:
        return self.target_rtp_units / self.unit_scale

    def multiplier_of(self, symbol: int) -> float:
        return self.multipliers[symbol]

    def units_of(self, symbol: int) -> int:
        return self.multiplier_units[symbol]

    def amount_from_units(self, payout_units: int) -> float:
        return payout_units / self.unit_scale * self.bet


DEFAULT_RULES = GameRules()
