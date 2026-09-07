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
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from simulation.tuning.study import run_study
from src.parameters import Parameters


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
    parser.add_argument(
        "--base-params",
        type=str,
        default=None,
        help="Path to base parameters JSON to inherit non-tuned groups from",
    )

    args = parser.parse_args()

    base_params = (
        Parameters.from_json(args.base_params) if args.base_params else None
    )

    print(
        f"Config: {args.n_trials} trials | {args.n_jobs} jobs | "
        f"Seats: {args.seats} | Seeds: {args.seeds} | Steps: {args.steps} vs '{args.baseline}'"
    )

    study, _ = run_study(
        study_name=args.study_name,
        storage=args.storage,
        n_trials=args.n_trials,
        n_jobs=args.n_jobs,
        groups=args.groups,
        baseline=args.baseline,
        seats=args.seats,
        seeds=args.seeds,
        steps=args.steps,
        output_path=args.output,
        base_params=base_params,
    )

    print("\n" + "=" * 60)
    print("Optimization Complete!")
    print(f"Total Trials   : {len(study.trials)}")
    print(f"Best Score     : {study.best_value:.1f}")
    print(f"Best Trial #   : {study.best_trial.number}")
    print("=" * 60)
    print(f"Saved optimal parameters to: {Path(args.output).resolve()}")


if __name__ == "__main__":
    main()
