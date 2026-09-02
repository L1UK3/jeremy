from economics.economy import (
    affordable_hires,
    best_crop,
    crop_cost,
    crop_roi,
    expansion_cost,
    max_daily_hires,
    next_quadrant_target,
    should_buy_seed,
    should_expand,
)
from environment.state import GameState


def test_economy_calculations():
    obs = {
        "player": 0,
        "step": 0,
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
        "private": {"shed": {}, "seeds": {}},
    }
    state = GameState.from_obs(obs)

    # Crop evaluation
    assert crop_cost("MELON") > 0
    assert crop_roi(state, "MELON") > 0
    assert best_crop(state) in ("MELON", "WHEAT", "CARROT")
    assert should_buy_seed(state, "MELON", target_count=1) is True

    # Land expansion
    assert expansion_cost(state) == 1000
    assert next_quadrant_target(state) == (5, 0)
    assert should_expand(state) is True

    # Farmhand hiring
    assert max_daily_hires(state) >= 4
    assert affordable_hires(state, max_hires_per_day=5, max_budget=100) >= 1
