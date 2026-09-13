"""Analyze top scoring episodes and extract supervised imitation datasets."""

from __future__ import annotations

import argparse
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

_dummy = types.ModuleType(
    "kaggle_environments.envs.open_spiel_env.open_spiel_env"
)
_dummy.ENV_REGISTRY = {}
_dummy.LAZY_ENV_LOADERS = {}
sys.modules["kaggle_environments.envs.open_spiel_env.open_spiel_env"] = _dummy

from data.imitation import process_parquet_dataset


def print_winning_profile(
    features_path: Path | str = Path(".out/episode_features.csv"),
) -> None:
    """Print high-level summary of top 5% winning strategies."""
    p = Path(features_path)
    if not p.is_file():
        print(f"Features file not found at {p}. Run data/features.py first.")
        return

    import pandas as pd

    df = pd.read_csv(p)
    top = df[df["final_money"] >= df["final_money"].quantile(0.95)]
    print("=== WINNING STRATEGY PROFILE (TOP 5%) ===")
    print(f"Mean Final Bank   : ${top['final_money'].mean():,.2f}")
    print(f"Mean Peak Crew    : {top['peak_crew'].mean():.1f} workers")
    print(f"Mean Total Hires  : {top['total_hires'].mean():.1f} hires")
    print(f"First Land Day    : Day {top['first_land_day'].median():.0f}")
    print(f"Mean Wheat Plants : {top['plants_wheat'].mean():.1f}")
    print(f"Mean Melon Plants : {top['plants_melon'].mean():.1f}")


def extract_imitation_data(
    top_percentile: float = 0.95,
    parquet_path: Path | str = Path(".out/replays.parquet"),
    features_csv: Path | str = Path(".out/episode_features.csv"),
    out_npz: Path | str = Path(".out/imitation_dataset.npz"),
) -> None:
    """Extract supervised imitation training dataset from top percentile replays."""
    p_path = Path(parquet_path)
    f_path = Path(features_csv)
    if not p_path.is_file():
        print(f"Parquet dataset not found at {p_path}.")
        return

    features, targets = process_parquet_dataset(
        parquet_path=p_path,
        features_csv_path=f_path if f_path.is_file() else None,
        top_percentile=top_percentile,
        out_npz_path=out_npz,
    )
    print(
        f"Saved {features.shape[0]} training samples to {out_npz} (labels: {list(targets.keys())})"
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyze episodes and extract imitation datasets."
    )
    parser.add_argument(
        "--extract-imitation",
        action="store_true",
        help="Extract imitation dataset from replays.parquet",
    )
    parser.add_argument(
        "--top-percentile",
        type=float,
        default=0.95,
        help="Top quantile cutoff (default: 0.95)",
    )
    parser.add_argument(
        "--out-npz",
        type=str,
        default=".out/imitation_dataset.npz",
        help="Output .npz path",
    )
    args = parser.parse_args()

    if args.extract_imitation:
        extract_imitation_data(
            top_percentile=args.top_percentile, out_npz=Path(args.out_npz)
        )
    else:
        print_winning_profile()


if __name__ == "__main__":
    main()
