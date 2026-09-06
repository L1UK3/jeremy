from __future__ import annotations

import inspect
from pathlib import Path
from typing import Any

from environment.board import Board
from environment.state import GameState


def _make_minimal_obs(
    step: int = 24,
    day: int = 1,
    hour: int = 0,
    farmer_pos: list[int] | None = None,
    weeds_coords: list[tuple[int, int]] | None = None,
    inventory: dict[str, int] | None = None,
) -> dict[str, Any]:
    """Build a minimal valid observation dictionary for unit testing."""
    tiles = [[None for _ in range(10)] for _ in range(10)]
    if weeds_coords:
        for wx, wy in weeds_coords:
            tiles[wy][wx] = {"kind": "WEED"}

    return {
        "player": 0,
        "step": step,
        "day": day,
        "hour": hour,
        "farms": [
            {
                "money": 1000,
                "tiles": tiles,
                "farmer": farmer_pos or [0, 0],
                "hands": [],
                "unlocked_quadrants": ["NW"],
                "hires_today": 0,
            },
            {
                "money": 1000,
                "tiles": [[None for _ in range(10)] for _ in range(10)],
                "farmer": [0, 0],
                "hands": [],
                "unlocked_quadrants": ["NW"],
                "hires_today": 0,
            },
        ],
        "private": {
            "shed": {},
            "seeds": {"WHEAT": 5},
            "inventories": [inventory or {}],
        },
        "market": {
            "inventory": {"WHEAT": 10000},
            "prices": {"WHEAT": 25},
        },
        "town": {
            "unlocked_shops": [],
        },
    }


def test_strategies_zero_trajectories_imports():
    """Verify that no strategy module imports from trajectories or references FLAT_TRACE."""
    strategies_dir = Path(__file__).resolve().parents[1] / "src" / "strategies"
    for py_file in strategies_dir.glob("*.py"):
        content = py_file.read_text(encoding="utf-8")
        assert "from trajectories" not in content, (
            f"{py_file.name} imports from trajectories"
        )
        assert "import trajectories" not in content, (
            f"{py_file.name} imports trajectories"
        )
        assert "FLAT_TRACE" not in content, (
            f"{py_file.name} references FLAT_TRACE"
        )


def test_no_trace_parameters_in_exported_strategy_functions():
    """Verify all callable exports in src.strategies do not accept trace parameters."""
    import src.strategies as strat

    for name in strat.__all__:
        obj = getattr(strat, name)
        if callable(obj) and not isinstance(obj, type):
            sig = inspect.signature(obj)
            param_names = [p.lower() for p in sig.parameters]
            assert "trace" not in param_names, (
                f"Strategy function '{name}' accepts 'trace' parameter"
            )
            assert "flat_trace" not in param_names, (
                f"Strategy function '{name}' accepts 'flat_trace' parameter"
            )


def test_trace_functions_removed_from_strategies():
    """Verify front_run, split, and weed_use_guarded are no longer exported."""
    import src.strategies as strat

    assert not hasattr(strat, "front_run"), (
        "front_run should be removed from strategies"
    )
    assert not hasattr(strat, "split"), (
        "split should be removed from strategies"
    )
    assert not hasattr(strat, "weed_use_guarded"), (
        "weed_use_guarded should be removed from strategies"
    )
    assert "front_run" not in strat.__all__
    assert "split" not in strat.__all__
    assert "weed_use_guarded" not in strat.__all__


def test_front_runner_file_deleted():
    """Verify front_runner.py has been removed from src/strategies."""
    front_runner_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "strategies"
        / "front_runner.py"
    )
    assert not front_runner_path.exists(), "front_runner.py should be deleted"


def test_weed_clear_state_based_dispatches_idle_unit():
    """Verify weed_clear_state_based assigns idle unit to clear nearest unlocked weed."""
    from src.strategies.weed_repair import weed_clear_state_based

    obs = _make_minimal_obs(
        step=24, day=1, hour=0, farmer_pos=[0, 0], weeds_coords=[(1, 0)]
    )
    state = GameState.from_obs(obs)
    board = Board(state)

    action = {"farmer": ["PASS"], "hands": [], "market": []}
    result = weed_clear_state_based(state, board, action)

    # Farmer is at (0, 0), weed is at (1, 0); farmer should step EAST toward weed
    assert result["farmer"] == ["EAST"]


def test_weed_clear_state_based_skips_when_inventory_not_empty():
    """Verify weed_clear_state_based skips units that have items in their inventory."""
    from src.strategies.weed_repair import weed_clear_state_based

    obs = _make_minimal_obs(
        step=24,
        day=1,
        hour=0,
        farmer_pos=[0, 0],
        weeds_coords=[(1, 0)],
        inventory={"WHEAT": 2},
    )
    state = GameState.from_obs(obs)
    board = Board(state)

    action = {"farmer": ["PASS"], "hands": [], "market": []}
    result = weed_clear_state_based(state, board, action)

    # Unit has items in inventory, should remain PASS
    assert result["farmer"] == ["PASS"]


def test_weed_clear_state_based_skips_unreachable_weeds():
    """Verify weed_clear_state_based skips weeds when remaining day turns are insufficient."""
    from src.strategies.weed_repair import weed_clear_state_based

    # Step 47 is hour 23 (last turn of day 1). Distance to (3, 3) is 6 steps, unreachable.
    obs = _make_minimal_obs(
        step=47, day=1, hour=23, farmer_pos=[0, 0], weeds_coords=[(3, 3)]
    )
    state = GameState.from_obs(obs)
    board = Board(state)

    action = {"farmer": ["PASS"], "hands": [], "market": []}
    result = weed_clear_state_based(state, board, action)

    assert result["farmer"] == ["PASS"]


def test_weed_clear_state_based_preserves_active_op():
    """Verify weed_clear_state_based does not overwrite an existing non-PASS action."""
    from src.strategies.weed_repair import weed_clear_state_based

    obs = _make_minimal_obs(
        step=24, day=1, hour=0, farmer_pos=[0, 0], weeds_coords=[(1, 0)]
    )
    state = GameState.from_obs(obs)
    board = Board(state)

    action = {"farmer": ["WATER"], "hands": [], "market": []}
    result = weed_clear_state_based(state, board, action)

    assert result["farmer"] == ["WATER"]


def test_weed_repair_productive_route():
    """Verify weed_repair_productive_route intercepts blocked op underfoot with DIG and replays next step."""
    from src.strategies.weed_repair import weed_repair_productive_route

    obs = _make_minimal_obs(
        step=24, day=1, hour=0, farmer_pos=[0, 0], weeds_coords=[(0, 0)]
    )
    state = GameState.from_obs(obs)
    board = Board(state)

    # Farmer is standing on a weed and tries to PLANT WHEAT
    action = {"farmer": ["PLANT", "WHEAT"], "hands": [], "market": []}
    result = weed_repair_productive_route(state, board, action)

    assert result["farmer"] == ["DIG"]


def test_debt_manager_opening():
    """Verify debt_manager.opening produces valid opening orders without trace."""
    from src.strategies.debt_manager import opening

    action = {"farmer": ["PASS"], "hands": [], "market": []}
    res0 = opening(action, step=0)
    assert any(
        o[0] == "BUY_PRODUCT" and o[1] == "WHEAT"
        for o in res0.get("market", [])
    )
