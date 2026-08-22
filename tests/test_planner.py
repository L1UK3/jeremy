import pytest

from agent.planner import Planner
from environment.actions import Action


@pytest.fixture
def mock_state():
    return {
        "current_tile": None,
        "inventory": {"corn_seed": 5, "corn": 10},
        "market_prices": {"corn": 2.0, "corn_seed": 1.0},
        "tiles": [
            {
                "x": 0,
                "y": 0,
                "kind": "PLANT",
                "crop": "corn",
                "yield_units": 5,
                "watered_today": True,
            },
            {
                "x": 1,
                "y": 0,
                "kind": "PLANT",
                "crop": "corn",
                "yield_units": 0,
                "watered_today": False,
            },
            {"x": 2, "y": 0, "kind": "EMPTY"},
        ],
        "hands": 2,
        "money": 100.0,
        "land": {"width": 3, "height": 1},
        "expandable_tiles": [{"x": 3, "y": 0}, {"x": 4, "y": 0}],
    }


@pytest.fixture
def mock_planner():
    return Planner(state=mock_state())


def test_evaluate_expansion():
    planner = mock_planner()
    expansion_action = Action("EXPAND", {"x": 3, "y": 0})
    score = planner.evaluate_action(expansion_action)
    assert score > 0, "Expansion action should have a positive score"
    assert score < 100, "Expansion action score should be reasonable"
    assert isinstance(score, float), "Score should be a float"
