from economy import Economy
from state import GameState


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
    eco = Economy(state)
    assert eco.crop_roi("MELON") > 0
    assert eco.affordable_hires(max_hires_per_day=5, max_budget=100) >= 1
