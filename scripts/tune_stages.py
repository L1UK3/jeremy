"""Sequential staged hyperparameter tuning across subsystem parameter batches.

Runs sequential Optuna studies for each subsystem parameter group, carrying forward
accumulated parameter improvements into each subsequent stage and persisting updates
to src/parameters.json.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from simulation.tuning.study import run_study
from src.parameters import Parameters

STAGE_DEFINITIONS: list[tuple[str, int, str]] = [
    ("market_maker", 25, "Liquidation timings, glut weights, and shed pressure"),
    ("procurement", 25, "Expansion schedule, crew hire thresholds, and animal buffers"),
    ("dispatcher", 35, "Spatial scheduling, chore priorities, and distance penalties"),
    ("explosion", 20, "Turn-672 terminal dump multipliers and glut penalties"),
    ("debt_manager", 10, "Opening liquidity and cash-management threshold"),
]


def run_staged_tuning(
    target_path: Path | str = "src/parameters.json",
    baseline: str = "simulation/base/main.py",
    selected_stages: list[str] | None = None,
    quick: bool = False,
    steps: int = 720,
) -> Parameters:
    """Execute tuning sequentially through each parameter batch."""
    out_path = Path(target_path).resolve()
    current_params = (
        Parameters.from_json(out_path)
        if out_path.is_file()
        else Parameters()
    )

    stages_to_run = [
        (name, 3 if quick else trials, desc)
        for name, trials, desc in STAGE_DEFINITIONS
        if selected_stages is None or name in selected_stages
    ]

    total_stages = len(stages_to_run)
    print("=" * 70)
    print(f"Staged Parameter Tuning ({total_stages} stages)")
    print(f"Target file: {out_path}")
    print(f"Baseline   : {baseline} ({steps} steps/game)")
    print("=" * 70)

    start_total = time.time()

    for idx, (group, trials, desc) in enumerate(stages_to_run, start=1):
        print(f"\n[{idx}/{total_stages}] Tuning batch: {group.upper()} ({trials} trials)")
        print(f"  Focus: {desc}")
        stage_start = time.time()

        study, current_params = run_study(
            study_name=f"tune_{group}_{int(time.time())}",
            n_trials=trials,
            n_jobs=1,
            groups=[group],
            baseline=baseline,
            seats=[0, 1],
            seeds=[42, 1337],
            steps=steps,
            output_path=out_path,
            base_params=current_params,
        )

        elapsed = time.time() - stage_start
        best_score = study.best_value
        print(
            f"  --> Completed {group} in {elapsed:.1f}s | Best score: {best_score:.1f} (Trial #{study.best_trial.number})"
        )
        print(f"  --> Updated {out_path}")

    total_elapsed = time.time() - start_total
    print("\n" + "=" * 70)
    print(f"All stages complete in {total_elapsed / 60:.1f} minutes.")
    print(f"Final parameters written to: {out_path}")
    print("=" * 70)

    return current_params


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sequential staged parameter tuning for Jeremy.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--target",
        "-o",
        type=str,
        default="src/parameters.json",
        help="Path to parameters.json to read base values and save updates",
    )
    parser.add_argument(
        "--baseline",
        "-b",
        type=str,
        default="simulation/base/main.py",
        help="Opponent baseline ('simulation/base/main.py', 'starter', or path)",
    )
    parser.add_argument(
        "--stages",
        "-s",
        nargs="+",
        default=None,
        choices=[name for name, _, _ in STAGE_DEFINITIONS],
        help="Specific stages to run (default: runs all in sequence)",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick smoke test mode (runs 3 trials per batch instead of full count)",
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=720,
        help="Game steps per match (default 720 full game)",
    )

    args = parser.parse_args()
    run_staged_tuning(
        target_path=args.target,
        baseline=args.baseline,
        selected_stages=args.stages,
        quick=args.quick,
        steps=args.steps,
    )


if __name__ == "__main__":
    main()
