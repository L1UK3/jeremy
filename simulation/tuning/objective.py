"""Optuna objective factory for evaluating agent parameter configurations."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

from simulation.episode import run_episode
from simulation.tuning.search_space import sample_parameters
from src.main import make_agent
from src.parameters import Parameters


def create_objective(
    groups: Sequence[str] | None = None,
    baseline: str = "starter",
    seats: Sequence[int] = (0, 1),
    seeds: Sequence[int] = (42, 1337),
    steps: int = 720,
    base_params: Parameters | None = None,
) -> Callable[[Any], float]:
    """Factory returning an Optuna objective function with fixed evaluation settings."""

    def objective(trial: Any) -> float:
        params = sample_parameters(trial, groups=groups, base=base_params)
        agent = make_agent(params)

        scores: list[float] = []
        for seat in seats:
            for _ in seeds:
                res = run_episode(
                    challenger=agent,
                    baseline=baseline,
                    seat=seat,
                    steps=steps,
                )

                scores.append(res.score_challenger)

        return float(sum(scores) / len(scores)) if scores else 0.0

    return objective
