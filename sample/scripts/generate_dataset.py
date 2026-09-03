"""Dataset generation CLI for Kaggriculture Behavioral Cloning.

Extracts demonstration (feature, macro_target) tuples from real match replays
generated in data/ and .out/ (e.g., replays.parquet, raw/*.json.gz).
"""

from __future__ import annotations

import argparse
import gzip
import json
import sys
from collections import Counter
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import numpy as np
import pyarrow.parquet as pq

# Ensure project root and src/ are on sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


from sample.simulation.episode import Episode
from sample.environment.board import Board
from sample.environment.encode import encode_state_1706
from sample.environment.state import GameState

CROPS = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON"]
CROP_TO_IDX = {c: i for i, c in enumerate(CROPS)}

REPLAY_SEARCH_CANDIDATES = [
    Path("data/replays.parquet"),
    Path(".out/replays.parquet"),
    Path(".out/episodes_dataset/replays.parquet"),
    Path("data/raw"),
    Path(".out/raw"),
    Path(".out/highest_scoring_replays"),
]


def resolve_replay_source(custom_path: str | Path | None = None) -> Path:
    """Resolve replay path from CLI argument or default candidates."""
    if custom_path:
        p = Path(custom_path)
        if p.exists():
            return p
        raise FileNotFoundError(
            f"Specified replays path does not exist: {custom_path}"
        )

    for candidate in REPLAY_SEARCH_CANDIDATES:
        if candidate.exists():
            if candidate.is_file() and candidate.suffix == ".parquet":
                return candidate
            if candidate.is_dir() and any(candidate.iterdir()):
                return candidate

    search_str = "\n  - ".join(str(c) for c in REPLAY_SEARCH_CANDIDATES)
    raise FileNotFoundError(
        f"No replay datasets found! Looked in:\n  - {search_str}\n"
        "Run the data scraper/repacker (e.g. data/scrape.py and data/repack.py), "
        "place replays.parquet in data/, or pass --replays <path>."
    )


def iter_replays(
    source_path: Path, max_episodes: int | None = None
) -> Iterator[tuple[int | str, dict[str, Any]]]:
    """Stream (episode_id, replay_dict) from a parquet file or directory of json/json.gz."""
    yielded = 0

    if source_path.is_file() and source_path.suffix == ".parquet":
        pf = pq.ParquetFile(source_path)
        for batch in pf.iter_batches(batch_size=10):
            tbl = batch.to_pydict()
            for eid, blob in zip(
                tbl["episode_id"], tbl["replay_json"], strict=False
            ):
                try:
                    replay_dict = json.loads(blob)
                    yield eid, replay_dict
                    yielded += 1
                    if max_episodes and yielded >= max_episodes:
                        return
                except Exception as e:
                    print(f"  Warning: failed to parse replay {eid}: {e}")

    elif source_path.is_dir():
        files = sorted(
            list(source_path.glob("*.json.gz"))
            + list(source_path.glob("*.json"))
        )
        for f in files:
            eid = f.stem.replace(".json", "")
            try:
                if f.name.endswith(".json.gz"):
                    with gzip.open(f, "rt", encoding="utf-8") as gz_f:
                        replay_dict = json.load(gz_f)
                else:
                    with open(f, encoding="utf-8") as json_f:
                        replay_dict = json.load(json_f)
                yield eid, replay_dict
                yielded += 1
                if max_episodes and yielded >= max_episodes:
                    return
            except Exception as e:
                print(f"  Warning: failed to parse file {f}: {e}")

    elif source_path.is_file():
        eid = source_path.stem.replace(".json", "")
        if source_path.name.endswith(".json.gz"):
            with gzip.open(source_path, "rt", encoding="utf-8") as gz_f:
                yield eid, json.load(gz_f)
        else:
            with open(source_path, encoding="utf-8") as json_f:
                yield eid, json.load(json_f)


ANIMALS = ["NONE", "COW", "SHEEP", "GOOSE"]
ANIMAL_TO_IDX = {a: i for i, a in enumerate(ANIMALS)}
PREDATION_MODES = ["BALANCED", "FRONT_RUN", "CORNER_FEED"]
PREDATION_TO_IDX = {m: i for i, m in enumerate(PREDATION_MODES)}


def extract_macro_targets_from_step(
    obs: dict[str, Any],
) -> tuple[int, int, np.ndarray, int, np.ndarray, int]:
    """Extract (crop_target_idx, crew_target_count, market_reservation_scales, animal_target_idx, crop_weights, predation_target_idx) from state."""
    state = GameState.from_obs(obs)
    crew_target = min(10, len(state.hands))

    crop_counts = dict.fromkeys(CROPS, 0)
    animal_counts = {"COW": 0, "SHEEP": 0, "GOOSE": 0}

    for r in range(state.board_size):
        for c in range(state.board_size):
            tile_data = state.tiles[r][c]
            if isinstance(tile_data, dict):
                crp = tile_data.get("crop")
                if crp in CROP_TO_IDX:
                    crop_counts[crp] += 1
                anim = tile_data.get("animal")
                if anim in animal_counts:
                    animal_counts[anim] += 1

    total_planted = sum(crop_counts.values())
    if total_planted > 0:
        crop_weights = np.array(
            [crop_counts[c] / float(total_planted) for c in CROPS],
            dtype=np.float32,
        )
    else:
        crop_weights = np.array([0.2, 0.2, 0.2, 0.2, 0.2], dtype=np.float32)

    best_c = max(crop_counts, key=lambda k: crop_counts[k])
    if crop_counts[best_c] == 0:
        best_c = "MELON" if state.price("MELON") >= 160 else "STRAWBERRY"
    crop_target = CROP_TO_IDX[best_c]

    # Animal Target
    dominant_anim = max(animal_counts, key=lambda k: animal_counts[k])
    if animal_counts[dominant_anim] > 0:
        animal_target = ANIMAL_TO_IDX[dominant_anim]
    else:
        animal_target = 0  # NONE

    # Predation Mode
    player = state.player
    farms = state.raw.get("farms") or []
    predation_target = 0  # BALANCED
    if len(farms) > 1:
        opp_farm = farms[1 - player]
        opp_wheat = int((opp_farm.get("inventory") or {}).get("WHEAT", 0) or 0)
        opp_animals = 0
        opp_shed = opp_farm.get("inventory") or {}
        opp_high_val = int(opp_shed.get("MELON", 0) or 0) + int(
            opp_shed.get("STRAWBERRY", 0) or 0
        )
        if opp_animals > 0 and opp_wheat < 3:
            predation_target = PREDATION_TO_IDX["CORNER_FEED"]
        elif opp_high_val >= 10:
            predation_target = PREDATION_TO_IDX["FRONT_RUN"]

    melon_res = min(1.0, float(state.shed.get("MELON", 0)) / 20.0)
    strawberry_res = min(1.0, float(state.shed.get("STRAWBERRY", 0)) / 30.0)
    milk_res = min(1.0, float(state.shed.get("MILK", 0)) / 15.0)
    wool_res = min(1.0, float(state.shed.get("WOOL", 0)) / 15.0)
    market_targets = np.array(
        [melon_res, strawberry_res, milk_res, wool_res], dtype=np.float32
    )

    return (
        crop_target,
        crew_target,
        market_targets,
        animal_target,
        crop_weights,
        predation_target,
    )


def get_seat_final_scores(replay: dict[str, Any]) -> tuple[float, float]:
    """Retrieve or compute final money / rewards for seat 0 and seat 1."""
    rewards = replay.get("rewards")
    if (
        rewards
        and len(rewards) == 2
        and (rewards[0] is not None or rewards[1] is not None)
    ):
        return float(rewards[0] or 0.0), float(rewards[1] or 0.0)

    steps = replay.get("steps") or []
    if not steps:
        return 0.0, 0.0

    last_step = steps[-1]
    score_0 = 0.0
    score_1 = 0.0

    try:
        if len(last_step) > 0 and "observation" in last_step[0]:
            farms = last_step[0]["observation"].get("farms") or []
            if len(farms) > 0:
                score_0 = float(farms[0].get("money", 0.0))
            if len(farms) > 1:
                score_1 = float(farms[1].get("money", 0.0))
    except Exception:
        pass

    return score_0, score_1


def generate_demonstrations_from_replays(
    source_path: Path | str | None = None,
    output_path: Path | str = "data/demos/bc_train_dataset.npz",
    max_episodes: int | None = None,
    min_score: float = 0.0,
    only_winners: bool = True,
    sample_interval: int = 24,
) -> None:
    """Extract BC demonstration samples from replay dataset."""
    resolved_source = resolve_replay_source(source_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Reading replays from: {resolved_source}")
    print(
        f"Filtering settings: only_winners={only_winners}, "
        f"min_score={min_score:,.0f}, sample_interval={sample_interval}, "
        f"max_episodes={max_episodes or 'all'}"
    )

    all_features: list[np.ndarray] = []
    all_crops: list[int] = []
    all_crews: list[int] = []
    all_markets: list[np.ndarray] = []
    all_animals: list[int] = []
    all_weights: list[np.ndarray] = []
    all_predations: list[int] = []

    episodes_scanned = 0
    episodes_used = 0
    winner_scores: list[float] = []

    for _eid, replay in iter_replays(
        resolved_source, max_episodes=max_episodes
    ):
        episodes_scanned += 1
        steps = replay.get("steps") or []
        if len(steps) < 24:
            continue

        score_0, score_1 = get_seat_final_scores(replay)

        # Determine target seats to learn from
        seats_to_process: list[int] = []
        if only_winners:
            winner_seat = 0 if score_0 >= score_1 else 1
            best_score = max(score_0, score_1)
            if best_score >= min_score:
                seats_to_process.append(winner_seat)
                winner_scores.append(best_score)
        else:
            if score_0 >= min_score:
                seats_to_process.append(0)
                winner_scores.append(score_0)
            if score_1 >= min_score:
                seats_to_process.append(1)
                winner_scores.append(score_1)

        if not seats_to_process:
            continue

        episodes_used += 1

        for seat in seats_to_process:
            for step_idx, step_data in enumerate(steps):
                if step_idx % sample_interval != 0:
                    continue

                if (
                    len(step_data) <= seat
                    or "observation" not in step_data[seat]
                ):
                    continue

                obs = step_data[seat]["observation"]
                if obs.get("player") is None:
                    obs["player"] = seat

                try:
                    s = GameState.from_obs(obs)
                    b = Board(s)
                    feat = encode_state_1706(s, b).copy()[0]
                    (
                        crop_t,
                        crew_t,
                        mkt_t,
                        anim_t,
                        w_t,
                        pred_t,
                    ) = extract_macro_targets_from_step(obs)

                    all_features.append(feat)
                    all_crops.append(crop_t)
                    all_crews.append(crew_t)
                    all_markets.append(mkt_t)
                    all_animals.append(anim_t)
                    all_weights.append(w_t)
                    all_predations.append(pred_t)
                except Exception:
                    # Skip malformed intermediate step
                    continue

        if episodes_used % 25 == 0 and episodes_used > 0:
            print(
                f"  Scanned {episodes_scanned} | Used {episodes_used} matches -> "
                f"{len(all_features)} samples collected..."
            )

    if not all_features:
        raise RuntimeError(
            f"No samples were generated from {episodes_scanned} scanned replays. "
            f"Check if --min-score={min_score} is too high."
        )

    features_arr = np.array(all_features, dtype=np.float32)
    crops_arr = np.array(all_crops, dtype=np.int64)
    crews_arr = np.array(all_crews, dtype=np.int64)
    markets_arr = np.array(all_markets, dtype=np.float32)
    animals_arr = np.array(all_animals, dtype=np.int64)
    weights_arr = np.array(all_weights, dtype=np.float32)
    predations_arr = np.array(all_predations, dtype=np.int64)

    np.savez_compressed(
        str(output_path),
        features=features_arr,
        crop_targets=crops_arr,
        crew_targets=crews_arr,
        market_targets=markets_arr,
        target_animals=animals_arr,
        crop_weights=weights_arr,
        predation_mode=predations_arr,
    )

    crop_counts = Counter(crops_arr)
    crew_counts = Counter(crews_arr)
    anim_counts = Counter(animals_arr)
    pred_counts = Counter(predations_arr)

    print("\n" + "=" * 60)
    print("DEMONSTRATION DATASET GENERATION COMPLETE")
    print("=" * 60)
    print(f"Source:                {resolved_source}")
    print(f"Episodes Scanned:      {episodes_scanned}")
    print(f"Episodes Retained:     {episodes_used}")
    print(f"Total Samples:         {len(features_arr):,}")
    if winner_scores:
        print(
            f"Mean Winner Bank:      ${np.mean(winner_scores):,.1f} "
            f"(Max: ${np.max(winner_scores):,.1f})"
        )
    print("Crop Target Breakdown:")
    for crop, idx in CROP_TO_IDX.items():
        cnt = crop_counts.get(idx, 0)
        pct = (cnt / len(crops_arr)) * 100
        print(f"  - {crop:<12}: {cnt:>5} ({pct:5.1f}%)")
    print("Animal Strategy Breakdown:")
    for anim, idx in ANIMAL_TO_IDX.items():
        cnt = anim_counts.get(idx, 0)
        pct = (cnt / len(animals_arr)) * 100
        print(f"  - {anim:<12}: {cnt:>5} ({pct:5.1f}%)")
    print("Predation Mode Breakdown:")
    for pred, idx in PREDATION_TO_IDX.items():
        cnt = pred_counts.get(idx, 0)
        pct = (cnt / len(predations_arr)) * 100
        print(f"  - {pred:<12}: {cnt:>5} ({pct:5.1f}%)")
    print("Crew Size Distribution:")
    for crew in range(min(11, max(crews_arr) + 1)):
        cnt = crew_counts.get(crew, 0)
        if cnt > 0:
            pct = (cnt / len(crews_arr)) * 100
            print(f"  - Hands {crew:>2}:    {cnt:>5} ({pct:5.1f}%)")
    print(f"Saved dataset to:      {output_path.resolve()}")
    print("=" * 60 + "\n")



def generate_demonstrations_from_simulation(
    n_episodes: int = 15,
    output_path: Path | str = "data/demos/bc_train_dataset.npz",
    agent_pool: list[tuple[str, str]] | None = None,
) -> None:
    """Fallback simulation generator."""
    if agent_pool is None:
        agent_pool = [
            ("src/main.py", "simulation/base/c95/main.py"),
            ("simulation/base/c95/main.py", "src/main.py"),
            ("src/main.py", "starter"),
        ]

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    all_features: list[np.ndarray] = []
    all_crops: list[int] = []
    all_crews: list[int] = []
    all_markets: list[np.ndarray] = []
    all_animals: list[int] = []
    all_weights: list[np.ndarray] = []
    all_predations: list[int] = []

    print(
        f"Generating demonstration dataset across {n_episodes} simulated matches..."
    )

    for ep_idx in range(n_episodes):
        agent1_path, agent2_path = agent_pool[ep_idx % len(agent_pool)]
        episode = Episode(agent1=agent1_path, agent2=agent2_path, debug=False)
        result = episode.run()
        target_seat = result.winner if result.winner in (0, 1) else 0

        for step_data in episode.env.steps:
            player_state = step_data[target_seat]
            obs = player_state.observation
            step = obs.get("step", 0)

            if step % 24 == 0:
                s = GameState.from_obs(obs)
                b = Board(s)
                feat = encode_state_1706(s, b).copy()[0]
                (
                    crop_t,
                    crew_t,
                    mkt_t,
                    anim_t,
                    w_t,
                    pred_t,
                ) = extract_macro_targets_from_step(obs)

                all_features.append(feat)
                all_crops.append(crop_t)
                all_crews.append(crew_t)
                all_markets.append(mkt_t)
                all_animals.append(anim_t)
                all_weights.append(w_t)
                all_predations.append(pred_t)

        print(
            f"  Finished Match {ep_idx + 1:02d}/{n_episodes} [{agent1_path} vs {agent2_path}] "
            f"-> Winner: Seat {target_seat} | Samples: {len(all_features)}"
        )

    features_arr = np.array(all_features, dtype=np.float32)
    crops_arr = np.array(all_crops, dtype=np.int64)
    crews_arr = np.array(all_crews, dtype=np.int64)
    markets_arr = np.array(all_markets, dtype=np.float32)
    animals_arr = np.array(all_animals, dtype=np.int64)
    weights_arr = np.array(all_weights, dtype=np.float32)
    predations_arr = np.array(all_predations, dtype=np.int64)

    np.savez_compressed(
        str(output_path),
        features=features_arr,
        crop_targets=crops_arr,
        crew_targets=crews_arr,
        market_targets=markets_arr,
        target_animals=animals_arr,
        crop_weights=weights_arr,
        predation_mode=predations_arr,
    )
    print(
        f"\nSuccessfully saved {len(features_arr)} simulated samples to {output_path}"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Extract Behavioral Cloning demonstration dataset from replays"
    )
    parser.add_argument(
        "--replays",
        type=str,
        default=None,
        help="Path to replays.parquet or directory of replay json/json.gz (defaults to auto-detecting data/replays.parquet or .out/replays.parquet)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/demos/bc_train_dataset.npz",
        help="Target .npz output path (default: data/demos/bc_train_dataset.npz)",
    )
    parser.add_argument(
        "--episodes",
        type=int,
        default=None,
        help="Maximum episodes to process (default: all available in replays)",
    )
    parser.add_argument(
        "--min-score",
        type=float,
        default=0.0,
        help="Minimum final score required to include demonstration (default: 0.0)",
    )
    parser.add_argument(
        "--sample-interval",
        type=int,
        default=24,
        help="Step sampling interval in turns (default: 24 for daily boundaries)",
    )
    parser.add_argument(
        "--all-seats",
        action="store_true",
        help="Extract from both seats if they meet min-score, rather than only the winner",
    )
    parser.add_argument(
        "--simulate",
        action="store_true",
        help="Fallback: run simulated matches instead of reading replay files",
    )

    args = parser.parse_args()

    if args.simulate:
        generate_demonstrations_from_simulation(
            n_episodes=args.episodes or 15,
            output_path=args.output,
        )
    else:
        generate_demonstrations_from_replays(
            source_path=args.replays,
            output_path=args.output,
            max_episodes=args.episodes,
            min_score=args.min_score,
            only_winners=not args.all_seats,
            sample_interval=args.sample_interval,
        )
