import sys
from pathlib import Path

from sample.scripts.generate_dataset import (
    extract_macro_targets_from_step,
    generate_demonstrations_from_replays,
    resolve_replay_source,
)
from sample.training.dataset import KaggricultureReplayDataset

# Ensure project root and src/ are in sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))


def test_resolve_replay_source():
    source = resolve_replay_source()
    assert source.exists()
    assert source.suffix == ".parquet" or source.is_dir()


def test_extract_macro_targets_from_step():
    obs = {
        "player": 0,
        "step": 0,
        "day": 0,
        "hour": 0,
        "market": {"prices": {"WHEAT": 25, "CARROT": 35, "MELON": 250}},
        "farms": [
            {
                "money": 3000,
                "farmer": [4, 4],
                "hands": [],
                "unlocked_quadrants": ["NW"],
                "tiles": [[None for _ in range(10)] for _ in range(10)],
            }
        ],
        "private": {"shed": {"MELON": 10}, "seeds": {}},
    }
    targets = extract_macro_targets_from_step(obs)
    crop_t, crew_t, mkt_t = targets[0], targets[1], targets[2]
    assert 0 <= crop_t < 5
    assert crew_t == 0
    assert mkt_t.shape == (4,)
    assert 0.0 <= mkt_t[0] <= 1.0


def test_generate_and_load_replays(tmp_path):
    out_npz = tmp_path / "test_dataset.npz"
    generate_demonstrations_from_replays(
        output_path=out_npz,
        max_episodes=2,
        sample_interval=24,
    )
    assert out_npz.exists()

    ds = KaggricultureReplayDataset.from_npz(out_npz)
    assert len(ds) > 0
    item = ds[0]
    features, crop_t, crew_t, market_t = item[0], item[1], item[2], item[3]
    assert features.shape == (1706,)
    assert 0 <= crop_t.item() < 5
    assert crew_t.item() >= 0
    assert market_t.shape == (4,)

