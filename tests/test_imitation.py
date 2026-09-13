"""Unit tests for supervised imitation target extraction from Kaggriculture replays."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from data.imitation import (
    CROP_TO_IDX,
    LIVESTOCK_TO_IDX,
    extract_daily_targets_from_steps,
    extract_dataset_from_replays,
    load_imitation_dataset,
    save_imitation_dataset,
)


def _make_dummy_step(
    step: int = 0,
    money: int = 3000,
    planted_crop: str = "WHEAT",
    hands_count: int = 2,
    placed_animal: str | None = None,
    sell_orders: list[list[Any]] | None = None,
) -> list[dict[str, Any]]:
    """Build a minimal valid step structure for testing target extraction."""
    day = step // 24
    hour = step % 24

    tiles: list[list[Any]] = [[None for _ in range(10)] for _ in range(10)]
    tiles[0][0] = {
        "kind": "PLANT",
        "crop": planted_crop,
        "planted_day": day,
        "watered_today": True,
        "yield_units": 0,
    }
    if placed_animal:
        tiles[3][4] = {
            "kind": "PASTURE" if placed_animal in ("COW", "SHEEP") else "COOP",
            "animal": placed_animal,
            "placed_day": day,
            "yield_units": 1,
            "fed_today": True,
        }

    hands = [[1, 1] for _ in range(hands_count)]

    farmer_action = ["PLANT", planted_crop] if hour == 0 else ["PASS"]
    market_action = sell_orders or []

    obs = {
        "player": 0,
        "step": step,
        "day": day,
        "hour": hour,
        "farms": [
            {
                "money": money,
                "farmer": [0, 0],
                "hands": hands,
                "hires_today": hands_count,
                "unlocked_quadrants": ["NW"],
                "tiles": tiles,
            },
            {
                "money": 3000,
                "farmer": [0, 0],
                "hands": [],
                "hires_today": 0,
                "unlocked_quadrants": ["NW"],
                "tiles": [[None for _ in range(10)] for _ in range(10)],
            },
        ],
        "private": {
            "shed": {"WHEAT": 5, "MELON": 2},
            "seeds": {"WHEAT": 10},
            "inventories": [{} for _ in range(hands_count + 1)],
        },
        "market": {
            "prices": {"WHEAT": 25, "MELON": 240, "STRAWBERRY": 115, "MILK": 150, "WOOL": 190},
            "inventory": {"WHEAT": 1000, "MELON": 100},
        },
    }

    action_0 = {
        "farmer": farmer_action,
        "hands": [["PASS"] for _ in range(hands_count)],
        "market": market_action,
    }
    action_1 = {
        "farmer": ["PASS"],
        "hands": [],
        "market": [],
    }

    return [
        {"action": action_0, "observation": obs, "reward": money},
        {"action": action_1, "observation": obs, "reward": 3000},
    ]


def test_extract_daily_targets_mock_steps() -> None:
    """Verify daily ground-truth target extraction across day boundaries."""
    steps: list[list[dict[str, Any]]] = []
    # Day 0: Wheat, 2 hands, GOOSE, selling MELON at 240
    for h in range(24):
        sell = [["SELL", "MELON", 1]] if h == 10 else []
        steps.append(
            _make_dummy_step(
                step=h,
                money=3000 + h * 10,
                planted_crop="WHEAT",
                hands_count=2,
                placed_animal="GOOSE",
                sell_orders=sell,
            )
        )

    # Day 1: Melon, 5 hands, COW
    for h in range(24):
        steps.append(
            _make_dummy_step(
                step=24 + h,
                money=3500 + h * 20,
                planted_crop="MELON",
                hands_count=5,
                placed_animal="COW",
            )
        )

    targets = extract_daily_targets_from_steps(steps, seat=0)
    assert len(targets) == 2

    t0 = targets[0]
    assert t0.day == 0
    assert t0.crop == "WHEAT"
    assert t0.crop_idx == CROP_TO_IDX["WHEAT"]
    assert t0.crew == 2
    assert t0.livestock == "GOOSE"
    assert t0.livestock_idx == LIVESTOCK_TO_IDX["GOOSE"]
    assert t0.features.shape == (1706,)
    assert t0.features.dtype == np.float32

    t1 = targets[1]
    assert t1.day == 1
    assert t1.crop == "MELON"
    assert t1.crop_idx == CROP_TO_IDX["MELON"]
    assert t1.crew == 5
    assert t1.livestock == "COW"
    assert t1.livestock_idx == LIVESTOCK_TO_IDX["COW"]


def test_extract_dataset_shapes_and_types() -> None:
    """extract_dataset_from_replays must yield normalized, typed tensors."""
    steps: list[list[dict[str, Any]]] = []
    for s in range(48):
        steps.append(_make_dummy_step(step=s, money=3000 + s * 10))

    replays = [
        {"steps": steps, "final_reward": 50000.0, "seat": 0},
        {"steps": steps, "final_reward": 60000.0, "seat": 0},
    ]

    features_matrix, targets_dict = extract_dataset_from_replays(replays, min_final_score=40000.0)
    assert features_matrix.shape == (4, 1706)
    assert features_matrix.dtype == np.float32

    assert "crop" in targets_dict and targets_dict["crop"].shape == (4,)
    assert targets_dict["crop"].dtype == np.int64

    assert "crew" in targets_dict and targets_dict["crew"].shape == (4,)
    assert targets_dict["crew"].dtype == np.int64

    assert "livestock" in targets_dict and targets_dict["livestock"].shape == (4,)
    assert targets_dict["livestock"].dtype == np.int64

    assert "predation" in targets_dict and targets_dict["predation"].shape == (4,)
    assert targets_dict["predation"].dtype == np.int64

    assert "market" in targets_dict and targets_dict["market"].shape == (4, 4)
    assert targets_dict["market"].dtype == np.float32


def test_save_and_load_imitation_dataset(tmp_path: Path) -> None:
    """Dataset serialization to .npz must preserve arrays and keys exactly."""
    out_file = tmp_path / "test_dataset.npz"
    features_matrix = np.random.randn(10, 1706).astype(np.float32)
    targets_dict = {
        "crop": np.random.randint(0, 5, size=(10,), dtype=np.int64),
        "crew": np.random.randint(0, 11, size=(10,), dtype=np.int64),
        "livestock": np.random.randint(0, 4, size=(10,), dtype=np.int64),
        "predation": np.random.randint(0, 3, size=(10,), dtype=np.int64),
        "market": np.random.uniform(0.0, 2.0, size=(10, 4)).astype(np.float32),
    }

    save_imitation_dataset(features_matrix, targets_dict, out_file)
    assert out_file.exists()

    loaded_features, loaded_targets = load_imitation_dataset(out_file)
    np.testing.assert_allclose(features_matrix, loaded_features, rtol=1e-5)
    for k in ("crop", "crew", "livestock", "predation", "market"):
        np.testing.assert_allclose(targets_dict[k], loaded_targets[k], rtol=1e-5)


def test_min_score_filtering() -> None:
    """Only replays meeting score criteria must be processed."""
    steps = [_make_dummy_step(step=0)]
    replays = [
        {"steps": steps, "final_reward": 1000.0, "seat": 0},
        {"steps": steps, "final_reward": 50000.0, "seat": 0},
    ]

    features_matrix, _ = extract_dataset_from_replays(replays, min_final_score=20000.0)
    # Only the 50,000 game should be included (1 day -> 1 row)
    assert features_matrix.shape[0] == 1


def test_process_parquet_dataset_min_final_score(tmp_path: Path) -> None:
    """process_parquet_dataset should filter episodes and seats by min_final_score."""
    import json

    import pandas as pd
    import pyarrow as pa
    import pyarrow.parquet as pq

    from data.imitation import process_parquet_dataset

    pq_file = tmp_path / "test_replays.parquet"
    csv_file = tmp_path / "test_features.csv"
    npz_file = tmp_path / "test_out.npz"

    # Step dummy
    steps_low = [_make_dummy_step(step=0, money=20000)]
    steps_high = [_make_dummy_step(step=0, money=150000)]

    schema = pa.schema([("episode_id", pa.int64()), ("replay_json", pa.string())])
    table = pa.Table.from_pydict(
        {
            "episode_id": [101, 102],
            "replay_json": [
                json.dumps({"steps": steps_low}),
                json.dumps({"steps": steps_high}),
            ],
        },
        schema=schema,
    )
    pq.write_table(table, pq_file)

    df = pd.DataFrame(
        [
            {"episode_id": 101, "seat": 0, "final_money": 20000},
            {"episode_id": 102, "seat": 0, "final_money": 150000},
        ]
    )
    df.to_csv(csv_file, index=False)

    features, _targets = process_parquet_dataset(
        parquet_path=pq_file,
        features_csv_path=csv_file,
        min_final_score=100000.0,
        out_npz_path=npz_file,
    )

    assert features.shape[0] == 1
    assert npz_file.is_file()

