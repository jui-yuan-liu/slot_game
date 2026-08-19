"""Search for any reel set that meets the RTP / win-rate spec."""

from __future__ import annotations

from dataclasses import dataclass
import math
import random

from slot_game.config import DEFAULT_RULES, GameRules
from slot_game.evaluate import Evaluator
from slot_game.models import ReelSet, Stats


@dataclass(frozen=True)
class SearchConfig:
    seed: int = 0
    max_steps: int = 80_000
    min_length: int = 8
    max_init_length: int = 16
    max_length: int = 28
    polish_every: int = 2500
    win_rate_penalty: float = 6.0
    start_temperature: float = 0.05
    symbol_weights: tuple[int, ...] = (50, 27, 14, 6, 3)
    run_choices: tuple[int, ...] = (1, 2, 2, 2, 3, 3, 4)


class SearchError(RuntimeError):
    pass


class ReelOptimizer:
    def __init__(
        self,
        rules: GameRules = DEFAULT_RULES,
        config: SearchConfig | None = None,
        evaluator: Evaluator | None = None,
    ) -> None:
        self.rules = rules
        self.config = config or SearchConfig()
        self.evaluator = evaluator or Evaluator(rules)

    def search(self) -> tuple[ReelSet, Stats]:
        cfg = self.config
        rng = random.Random(cfg.seed)
        current = self._random_reel_set(rng)
        current_stats = self.evaluator.evaluate(current)
        current_score = self._score(current_stats)
        best, best_score = current, current_score

        for step in range(cfg.max_steps):
            if current_stats.valid():
                return current, current_stats

            try:
                candidate = self._mutate(current, rng)
                cand_stats = self.evaluator.evaluate(candidate)
            except ValueError:
                continue

            cand_score = self._score(cand_stats)
            temperature = cfg.start_temperature * (1.0 - step / cfg.max_steps) + 1e-4
            accept = cand_score <= current_score or rng.random() < math.exp(
                (current_score - cand_score) / temperature
            )
            if accept:
                current, current_stats, current_score = candidate, cand_stats, cand_score
                if cand_score < best_score:
                    best, best_score = candidate, cand_score

            if step % cfg.polish_every == cfg.polish_every - 1 and current_stats.win_rate >= self.rules.min_win_rate:
                polished, polished_stats = self._polish(current)
                if polished_stats.valid():
                    return polished, polished_stats
                pscore = self._score(polished_stats)
                if pscore < current_score:
                    current, current_stats, current_score = polished, polished_stats, pscore

        polished, polished_stats = self._polish(best)
        if polished_stats.valid():
            return polished, polished_stats
        raise SearchError(
            f"search failed: rtp={polished_stats.rtp:.8f} exact={polished_stats.exact_rtp} "
            f"win_rate={polished_stats.win_rate:.8f}"
        )

    def _score(self, stats: Stats) -> float:
        n = stats.n_combinations
        rtp_err = abs(stats.payout_units - self.rules.target_rtp_units * n) / (self.rules.unit_scale * n)
        wr_pen = max(0.0, self.rules.min_win_rate - stats.win_rate) * self.config.win_rate_penalty
        return rtp_err + wr_pen

    def _random_reel_set(self, rng: random.Random) -> ReelSet:
        strips = [
            self._random_strip(rng, rng.randint(self.config.min_length, self.config.max_init_length))
            for _ in range(self.rules.n_reels)
        ]
        return ReelSet.from_lists(strips, self.rules)

    def _random_strip(self, rng: random.Random, length: int) -> list[int]:
        reel: list[int] = []
        ids = list(self.rules.symbol_ids)
        while len(reel) < length:
            symbol = rng.choices(ids, weights=list(self.config.symbol_weights), k=1)[0]
            run = min(length - len(reel), rng.choice(self.config.run_choices))
            reel.extend([symbol] * run)
        return reel

    def _mutate(self, reel_set: ReelSet, rng: random.Random) -> ReelSet:
        out = reel_set.to_lists()
        kind = rng.randrange(6)
        reel = out[rng.randrange(self.rules.n_reels)]
        n = len(reel)
        if kind == 0 and n > self.rules.min_reel_length:
            del reel[rng.randrange(n)]
        elif kind == 1 and n < self.config.max_length:
            reel.insert(rng.randrange(n + 1), rng.randrange(self.rules.n_symbols))
        elif kind == 2 and n >= 2:
            i, j = rng.randrange(n), rng.randrange(n)
            reel[i], reel[j] = reel[j], reel[i]
        elif kind == 3:
            i = rng.randrange(n)
            reel[(i + 1) % n] = reel[i]
        elif kind == 4:
            i = rng.randrange(n)
            reel[(i + 1) % n] = (reel[i] + 1) % self.rules.n_symbols
        else:
            reel[rng.randrange(n)] = rng.randrange(self.rules.n_symbols)
        return ReelSet.from_lists(out, self.rules)

    def _polish(self, reel_set: ReelSet) -> tuple[ReelSet, Stats]:
        current = reel_set.to_lists()
        stats = self.evaluator.evaluate(ReelSet.from_lists(current, self.rules))
        best_err = abs(stats.payout_units - self.rules.target_rtp_units * stats.n_combinations)

        improved = True
        while improved:
            improved = False
            if stats.valid():
                return ReelSet.from_lists(current, self.rules), stats
            for reel in current:
                for i, old in enumerate(reel):
                    for new in self.rules.symbol_ids:
                        if new == old:
                            continue
                        reel[i] = new
                        cand = self.evaluator.evaluate(ReelSet.from_lists(current, self.rules))
                        err = abs(cand.payout_units - self.rules.target_rtp_units * cand.n_combinations)
                        if cand.win_rate >= self.rules.min_win_rate and err < best_err:
                            best_err = err
                            stats = cand
                            old = new
                            improved = True
                            if stats.valid():
                                return ReelSet.from_lists(current, self.rules), stats
                        else:
                            reel[i] = old
        return ReelSet.from_lists(current, self.rules), stats


def search(seed: int = 0, max_steps: int = 80_000) -> tuple[list[list[int]], Stats]:
    optimizer = ReelOptimizer(config=SearchConfig(seed=seed, max_steps=max_steps))
    reel_set, stats = optimizer.search()
    return reel_set.to_lists(), stats
