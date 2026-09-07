"""Optuna study creation, optimization, and parameter persistence."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import optuna

from simulation.tuning.objective import create_objective
from simulation.tuning.search_space import sample_parameters
from src.parameters import Parameters


def run_study(
    *,
    study_name: str = "kaggriculture_tuning",
    storage: str | None = None,
    n_trials: int = 30,
    n_jobs: int = 1,
    groups: Sequence[str] | None = None,
    baseline: str = "starter",
    seats: Sequence[int] = (0, 1),
    seeds: Sequence[int] = (42, 1337),
    steps: int = 720,
    output_path: str | Path | None = ".out/best_parameters.json",
    base_params: Parameters | None = None,
    seed: int = 42,
    show_progress_bar: bool | None = None,
) -> tuple[optuna.Study, Parameters]:
    """Create and optimize an Optuna study, saving the best parameters to disk."""
    if groups is not None and "all" not in groups:
        invalid = [g for g in groups if g not in Parameters.GROUPS]
        if invalid:
            raise ValueError(
                f"Unknown groups: {invalid}. Valid groups: {list(Parameters.GROUPS)}"
            )
        selected_groups: list[str] | None = list(groups)
    else:
        selected_groups = None

    study = optuna.create_study(
        study_name=study_name,
        storage=storage,
        load_if_exists=True,
        direction="maximize",
        sampler=optuna.samplers.TPESampler(seed=seed),
    )

    objective_fn = create_objective(
        groups=selected_groups,
        baseline=baseline,
        seats=seats,
        seeds=seeds,
        steps=steps,
        base_params=base_params,
    )

    if show_progress_bar is None:
        show_progress_bar = n_jobs == 1

    study.optimize(
        objective_fn,
        n_trials=n_trials,
        n_jobs=n_jobs,
        show_progress_bar=show_progress_bar,
    )

    best_params = sample_parameters(
        study.best_trial,
        groups=selected_groups,
        base=base_params,
    )

    if output_path is not None:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        best_params.to_json(out)

    return study, best_params
