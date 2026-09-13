"""Supervised imitation target extraction from Kaggriculture replays."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from src.model.encoder import encode_observation

__all__ = [
    "BASE_PRICES",
    "CROP_TO_IDX",
    "LIVESTOCK_TO_IDX",
    "MARKET_ITEMS",
    "PREDATION_TO_IDX",
    "DailyTarget",
    "extract_daily_targets_from_steps",
    "extract_dataset_from_replays",
    "load_imitation_dataset",
    "process_parquet_dataset",
    "save_imitation_dataset",
]

CROP_TO_IDX: dict[str, int] = {
    "WHEAT": 0,
    "CARROT": 1,
    "TOMATO": 2,
    "STRAWBERRY": 3,
    "MELON": 4,
}
LIVESTOCK_TO_IDX: dict[str, int] = {
    "NONE": 0,
    "COW": 1,
    "SHEEP": 2,
    "GOOSE": 3,
}
PREDATION_TO_IDX: dict[str, int] = {
    "Balanced": 0,
    "Front-run": 1,
    "Corner-feed": 2,
}
MARKET_ITEMS: tuple[str, ...] = ("MELON", "STRAWBERRY", "MILK", "WOOL")
BASE_PRICES: dict[str, float] = {
    "MELON": 250.0,
    "STRAWBERRY": 120.0,
    "MILK": 160.0,
    "WOOL": 200.0,
}


@dataclass(slots=True)
class DailyTarget:
    """Supervised macro policy target for one day of game play."""

    day: int
    crop: str
    crop_idx: int
    crew: int
    livestock: str
    livestock_idx: int
    predation: str
    predation_idx: int
    market_reservation_scales: dict[str, float]
    features: np.ndarray


def _find_active_crop(farm: dict[str, Any]) -> str:
    """Identify the predominant crop on the farm tiles."""
    crop_counts: Counter[str] = Counter(
        tile["crop"]
        for row in farm.get("tiles", []) or []
        for tile in row or []
        if isinstance(tile, dict)
        and tile.get("kind") == "PLANT"
        and tile.get("crop") in CROP_TO_IDX
    )
    return crop_counts.most_common(1)[0][0] if crop_counts else "WHEAT"


def _find_active_livestock(farm: dict[str, Any]) -> str:
    """Identify active livestock species housed on farm tiles."""
    for row in farm.get("tiles", []) or []:
        for tile in row or [] if isinstance(row, list) else []:
            if isinstance(tile, dict):
                animal = tile.get("animal")
                if animal in LIVESTOCK_TO_IDX and animal != "NONE":
                    return str(animal)
    return "NONE"


def extract_daily_targets_from_steps(
    steps: list[list[dict[str, Any]]], seat: int = 0
) -> list[DailyTarget]:
    """Extract daily observation features and ground-truth decisions for one seat."""
    targets: list[DailyTarget] = []
    total_steps = len(steps)
    total_days = (total_steps + 23) // 24

    for day in range(total_days):
        start_step = day * 24
        if start_step >= total_steps:
            break

        seat_entry = (
            steps[start_step][seat]
            if seat < len(steps[start_step])
            else steps[start_step][0]
        )
        obs = seat_entry.get("observation")
        if not obs:
            continue

        obs_copy = dict(obs)
        obs_copy["step"] = start_step
        obs_copy["player"] = seat
        features = encode_observation(obs_copy).squeeze(0).astype(np.float32)
        day_steps = steps[start_step : min(total_steps, (day + 1) * 24)]


        plant_counts: Counter[str] = Counter()
        max_crew = 0
        sells_by_item: dict[str, list[float]] = {k: [] for k in MARKET_ITEMS}
        early_sells = 0
        late_sells = 0

        for step_record in day_steps:
            p_seat = (
                step_record[seat] if seat < len(step_record) else step_record[0]
            )
            act = p_seat.get("action") or {}
            p_obs = p_seat.get("observation") or {}
            farms = p_obs.get("farms", [])

            if farms and len(farms) > seat:
                my_farm = farms[seat]
                hands_count = len(my_farm.get("hands", []))
                max_crew = max(
                    max_crew,
                    hands_count,
                    int(my_farm.get("hires_today", hands_count)),
                )

            # Count PLANT actions
            for unit_act in [
                act.get("farmer") or [],
                *(act.get("hands") or []),
            ]:
                if (
                    len(unit_act) >= 2
                    and unit_act[0] == "PLANT"
                    and unit_act[1] in CROP_TO_IDX
                ):
                    plant_counts[unit_act[1]] += 1

            # Count SELL actions and prices
            prices = p_obs.get("market", {}).get("prices", {})
            hour = p_obs.get("hour", 0)
            for order in act.get("market") or []:
                if (
                    isinstance(order, list)
                    and len(order) >= 2
                    and order[0] == "SELL"
                ):
                    item = order[1]
                    if item in sells_by_item and item in prices:
                        sells_by_item[item].append(float(prices[item]))
                        if hour < 12:
                            early_sells += 1
                        else:
                            late_sells += 1

        farms = obs.get("farms", [])
        primary_crop = (
            plant_counts.most_common(1)[0][0]
            if plant_counts
            else (
                _find_active_crop(farms[seat])
                if farms and len(farms) > seat
                else "WHEAT"
            )
        )
        livestock = (
            _find_active_livestock(farms[seat])
            if farms and len(farms) > seat
            else "NONE"
        )

        market_scales = {
            item: float(
                np.clip(min(sells_by_item[item]) / BASE_PRICES[item], 0.0, 2.0)
            )
            if sells_by_item[item]
            else 1.0
            for item in MARKET_ITEMS
        }

        predation = (
            "Front-run"
            if early_sells > late_sells and early_sells > 2
            else "Balanced"
        )

        targets.append(
            DailyTarget(
                day=day,
                crop=primary_crop,
                crop_idx=CROP_TO_IDX[primary_crop],
                crew=max(0, min(10, max_crew)),
                livestock=livestock,
                livestock_idx=LIVESTOCK_TO_IDX[livestock],
                predation=predation,
                predation_idx=PREDATION_TO_IDX[predation],
                market_reservation_scales=market_scales,
                features=features,
            )
        )

    return targets


def extract_dataset_from_replays(
    replays: list[Any],
    min_final_score: float | None = None,
    top_percentile: float | None = None,
) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    """Extract training feature matrix and label dictionaries from replay objects."""
    scores = [
        float(r.get("final_reward") or r.get("score") or 0.0)
        for r in replays
        if isinstance(r, dict)
    ]

    cutoff = min_final_score or 0.0
    if top_percentile is not None and scores:
        cutoff = max(cutoff, float(np.percentile(scores, top_percentile * 100)))

    (
        all_features,
        all_crops,
        all_crews,
        all_livestock,
        all_predation,
        all_market,
    ) = ([], [], [], [], [], [])

    for r in replays:
        if not isinstance(r, dict):
            continue
        reward = float(r.get("final_reward") or r.get("score") or 0.0)
        if reward < cutoff:
            continue

        for dt in extract_daily_targets_from_steps(
            r.get("steps") or [], seat=int(r.get("seat", 0))
        ):
            all_features.append(dt.features)
            all_crops.append(dt.crop_idx)
            all_crews.append(dt.crew)
            all_livestock.append(dt.livestock_idx)
            all_predation.append(dt.predation_idx)
            all_market.append(
                [dt.market_reservation_scales[item] for item in MARKET_ITEMS]
            )

    if not all_features:
        return np.empty((0, 1706), dtype=np.float32), {
            "crop": np.empty((0,), dtype=np.int64),
            "crew": np.empty((0,), dtype=np.int64),
            "livestock": np.empty((0,), dtype=np.int64),
            "predation": np.empty((0,), dtype=np.int64),
            "market": np.empty((0, 4), dtype=np.float32),
        }

    return np.vstack(all_features).astype(np.float32), {
        "crop": np.array(all_crops, dtype=np.int64),
        "crew": np.array(all_crews, dtype=np.int64),
        "livestock": np.array(all_livestock, dtype=np.int64),
        "predation": np.array(all_predation, dtype=np.int64),
        "market": np.array(all_market, dtype=np.float32),
    }


def save_imitation_dataset(
    features_matrix: np.ndarray,
    targets_dict: dict[str, np.ndarray],
    path: Path | str,
) -> None:
    """Save imitation features and target arrays to a compressed .npz archive."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        p,
        features=features_matrix,
        crop=targets_dict["crop"],
        crew=targets_dict["crew"],
        livestock=targets_dict["livestock"],
        predation=targets_dict["predation"],
        market=targets_dict["market"],
    )


def load_imitation_dataset(
    path: Path | str,
) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    """Load imitation dataset from a compressed .npz archive."""
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"Imitation dataset not found: {p}")
    with np.load(p) as data:
        key = "features" if "features" in data else "X"
        return data[key].astype(np.float32), {
            "crop": data["crop"].astype(np.int64),
            "crew": data["crew"].astype(np.int64),
            "livestock": data["livestock"].astype(np.int64),
            "predation": data["predation"].astype(np.int64),
            "market": data["market"].astype(np.float32),
        }


def process_parquet_dataset(
    parquet_path: Path | str,
    features_csv_path: Path | str | None = None,
    top_percentile: float | None = 0.95,
    out_npz_path: Path | str = Path(".out/imitation_dataset.npz"),
    min_final_score: float | None = None,
) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    """Parse top winning games from replays.parquet into an imitation training dataset."""
    import pandas as pd
    import pyarrow.dataset as pads

    p_path = Path(parquet_path)
    if not p_path.is_file():
        raise FileNotFoundError(f"Parquet dataset not found: {p_path}")

    top_episode_ids: set[int] = set()
    if features_csv_path and Path(features_csv_path).is_file():
        df = pd.read_csv(features_csv_path)
        if min_final_score is not None:
            top_episode_ids = set(
                df[df["final_money"] >= min_final_score]["episode_id"]
            )
        elif top_percentile is not None:
            top_episode_ids = set(
                df[df["final_money"] >= df["final_money"].quantile(top_percentile)][
                    "episode_id"
                ]
            )

    replays: list[dict[str, Any]] = []
    scanner = pads.dataset(str(p_path), format="parquet").scanner()
    for batch in scanner.to_batches():
        for _, row in batch.to_pandas().iterrows():
            ep_id = int(row.get("episode_id", 0))
            if top_episode_ids and ep_id not in top_episode_ids:
                continue
            raw = row.get("replay_json")
            if not raw:
                continue
            steps = json.loads(raw).get("steps") or []
            if steps:
                for seat in (0, 1):
                    replays.append(
                        {
                            "steps": steps,
                            "final_reward": steps[-1][seat].get("reward", 0.0),
                            "seat": seat,
                        }
                    )

    features, targets = extract_dataset_from_replays(
        replays,
        min_final_score=min_final_score,
        top_percentile=top_percentile if min_final_score is None else None,
    )
    save_imitation_dataset(features, targets, out_npz_path)
    return features, targets

