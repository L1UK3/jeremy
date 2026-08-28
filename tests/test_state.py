from src.state import GameState


def test_game_state_parsing():
    obs = {
        "player": 0,
        "step": 0,
        "market": {"prices": {"WHEAT": 25, "CARROT": 35}},
        "farms": [
            {
                "money": 3000,
                "farmer": [4, 4],
                "hands": [],
                "unlocked_quadrants": ["NW"],
                "tiles": [[None for _ in range(10)] for _ in range(10)],
            }
        ],
        "private": {"shed": {"WHEAT": 5}, "seeds": {}},
    }
    state = GameState.from_obs(obs)
    assert state.step == 0
    assert state.day == 0
    assert state.hour == 0
    assert state.money == 3000
    assert state.farmer == (4, 4)
    assert state.price("WHEAT") == 25
    assert state.inventory("WHEAT") == 5
    assert state.is_shed_adjacent(4, 4) is True
    assert state.is_shed_adjacent(0, 0) is False
