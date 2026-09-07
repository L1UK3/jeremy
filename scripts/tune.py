"""Hyperparameter optimization CLI using Optuna.

Tunes macro economic and spatial dispatching hyperparameters against simulation
baselines with support for multi-processing and targeted parameter groups.

Usage:
------
# Quick smoke test:
python scripts/tune.py --n-trials 3 --steps 24 --groups procurement

# Parallel tuning of market liquidation on starter baseline:
python scripts/tune.py --n-trials 50 --n-jobs 4 --groups market_maker

# Full tuning across all subsystems with persistent SQLite storage:
python scripts/tune.py --n-trials 100 --n-jobs 4 --storage sqlite:///.out/optuna.db
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

import optuna

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from main import make_agent
from parameters import Parameters
from simulation.episode import run_episode


def create_objective(
    groups: Sequence[str] | None,
    baseline: str,
    seats: Sequence[int],
    seeds: Sequence[int],
    steps: int,
):
    """Factory returning an Optuna objective function with fixed evaluation settings."""

    def objective(trial: optuna.Trial) -> float:
        params = Parameters.from_trial(trial, groups=groups)
        agent = make_agent(params)

        scores: list[float] = []
        for seat in seats:
            for seed in seeds:
                res = run_episode(
                    challenger=agent,
                    baseline=baseline,
                    seat=seat,
                    seed=seed,
                    steps=steps,
                    save_replay=False,
                )
                # Penalize timeouts, exceptions, or disqualified runs heavily
                if res.status_challenger != "DONE" or res.error_challenger:
                    return -1.0

                scores.append(res.score_challenger)

        return float(sum(scores) / len(scores)) if scores else 0.0

    return objective


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Optimize Kaggriculture hyperparameters via Optuna.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--n-trials",
        "-n",
        type=int,
        default=30,
        help="Total number of Optuna trials to run",
    )
    parser.add_argument(
        "--n-jobs",
        "-j",
        type=int,
        default=1,
        help="Number of concurrent worker processes for trial evaluation",
    )
    parser.add_argument(
        "--groups",
        "-g",
        nargs="+",
        default=["all"],
        help=(
            f"Subsystem groups to tune: 'all' or subset of {list(Parameters.GROUPS)}"
        ),
    )
    parser.add_argument(
        "--baseline",
        "-b",
        type=str,
        default="starter",
        help="Opponent baseline agent ('starter', 'random', or file path)",
    )
    parser.add_argument(
        "--steps",
        "-s",
        type=int,
        default=720,
        help="Match duration in turns",
    )
    parser.add_argument(
        "--seats",
        nargs="+",
        type=int,
        default=[0, 1],
        help="Player seats to evaluate (0, 1, or both)",
    )
    parser.add_argument(
        "--seeds",
        nargs="+",
        type=int,
        default=[42, 1337],
        help="Random seeds for game simulations",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=".out/best_parameters.json",
        help="Output JSON path for best parameters",
    )
    parser.add_argument(
        "--study-name",
        type=str,
        default="kaggriculture_tuning",
        help="Optuna study name",
    )
    parser.add_argument(
        "--storage",
        type=str,
        default=None,
        help="Database storage URI (e.g. 'sqlite:///.out/optuna.db')",
    )

    args = parser.parse_args()

    # Determine targeted groups
    if "all" in args.groups:
        selected_groups: list[str] | None = None
        print("Tuning all parameter groups simultaneously.")
    else:
        invalid = [g for g in args.groups if g not in Parameters.GROUPS]
        if invalid:
            print(
                f"Error: Unknown groups {invalid}. Valid: {list(Parameters.GROUPS)}"
            )
            sys.exit(1)
        selected_groups = list(args.groups)
        print(f"Tuning targeted groups: {selected_groups}")

    print(
        f"Config: {args.n_trials} trials | {args.n_jobs} jobs | "
        f"Seats: {args.seats} | Seeds: {args.seeds} | Steps: {args.steps} vs '{args.baseline}'"
    )

    study = optuna.create_study(
        study_name=args.study_name,
        storage=args.storage,
        load_if_exists=True,
        direction="maximize",
        sampler=optuna.samplers.TPESampler(seed=42),
    )

    objective_fn = create_objective(
        groups=selected_groups,
        baseline=args.baseline,
        seats=args.seats,
        seeds=args.seeds,
        steps=args.steps,
    )

    study.optimize(
        objective_fn,
        n_trials=args.n_trials,
        n_jobs=args.n_jobs,
        show_progress_bar=(args.n_jobs == 1),
    )

    print("\n" + "=" * 60)
    print("Optimization Complete!")
    print(f"Total Trials   : {len(study.trials)}")
    print(f"Best Score     : {study.best_value:.1f}")
    print(f"Best Trial #   : {study.best_trial.number}")
    print("=" * 60)

    # Export best parameters
    best_params = Parameters.from_trial(
        study.best_trial, groups=selected_groups
    )
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    best_params.to_json(out_path)
    print(f"Saved optimal parameters to: {out_path.resolve()}")


if __name__ == "__main__":
    main()
