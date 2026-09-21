"""Unit tests for the autonomous two-stage agent entrypoint (main.py)."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

import src.main as main
from src.main import agent, make_agent


def make_obs(
    step: int = 0,
    day: int = 0,
    hour: int = 0,
    money: int = 3000,
    farmer: tuple[int, int] = (2, 2),
    hands: list[list[int]] | None = None,
    shed: dict[str, int] | None = None,
    seeds: dict[str, int] | None = None,
    inventories: list[dict[str, int]] | None = None,
    tiles: list[list[Any]] | None = None,
    unlocked_quadrants: list[str] | None = None,
    prices: dict[str, int] | None = None,
) -> dict[str, Any]:
    """Construct realistic observation dict for agent testing."""
    if tiles is None:
        tiles = [[None for _ in range(10)] for _ in range(10)]
    quads = unlocked_quadrants or ["NW"]
    default_prices = {
        "WHEAT": 25,
        "CARROT": 35,
        "TOMATO": 60,
        "STRAWBERRY": 120,
        "MELON": 250,
        "MILK": 160,
        "WOOL": 200,
    }
    if prices:
        default_prices.update(prices)

    invs = inventories if inventories is not None else [{}]

    return {
        "player": 0,
        "step": step,
        "day": day,
        "hour": hour,
        "farms": [
            {
                "money": money,
                "tiles": tiles,
                "farmer": list(farmer),
                "hands": hands or [],
                "unlocked_quadrants": quads,
                "hires_today": len(hands or []),
            },
            {
                "money": 3000,
                "tiles": [[None for _ in range(10)] for _ in range(10)],
                "farmer": [2, 2],
                "hands": [],
                "unlocked_quadrants": ["NW"],
                "hires_today": 0,
            },
        ],
        "private": {
            "shed": shed or {},
            "seeds": seeds or {},
            "inventories": invs,
        },
        "market": {
            "inventory": {
                "WHEAT": 800,
                "CARROT": 600,
                "TOMATO": 400,
                "STRAWBERRY": 200,
                "MELON": 150,
                "MILK": 150,
                "WOOL": 150,
            },
            "prices": default_prices,
        },
        "town": {
            "unlocked_shops": ["BAKERY"],
        },
    }


def test_agent_runs_without_trace_dependencies() -> None:
    """Agent and its dependencies must not import or reference static trajectories."""
    assert "trajectories" not in sys.modules
    assert not hasattr(main, "FLAT_TRACE")


def test_macro_policy_evaluated_on_day_boundary() -> None:
    """Neural macro policy get_plan must be evaluated once per day and cached."""
    obs_day0_h0 = make_obs(step=0, day=0, hour=0)
    obs_day0_h1 = make_obs(step=1, day=0, hour=1)
    obs_day1_h0 = make_obs(step=24, day=1, hour=0)

    with patch("src.main.get_plan", wraps=None) as mock_get_plan:
        mock_get_plan.return_value = {
            "crop": "WHEAT",
            "crew": 0,
            "market": {},
            "livestock": "NONE",
            "predation": "Balanced",
        }

        # Step 0: should call get_plan
        _ = agent(obs_day0_h0)
        assert mock_get_plan.call_count == 1

        # Step 1 (same day): should use cached plan without calling get_plan
        _ = agent(obs_day0_h1)
        assert mock_get_plan.call_count == 1

        # Step 24 (day 1): should call get_plan again
        _ = agent(obs_day1_h0)
        assert mock_get_plan.call_count == 2


def test_stage1_procurement_and_market_orders() -> None:
    """Stage 1 orders seeds and market actions, strictly capped at 10 orders."""
    obs = make_obs(step=2, day=0, hour=2, money=3000, seeds={})
    act = agent(obs)

    assert "market" in act
    assert isinstance(act["market"], list)
    assert len(act["market"]) <= 10
    # Must order seeds since tiles are empty and seeds are 0
    has_seed_buy = any(o[0] == "BUY_SEED" for o in act["market"])
    assert has_seed_buy


def test_stage2_spatial_dispatcher_coordinates_units() -> None:
    """Stage 2 must dispatch productive chores to farmer and all hands."""
    obs = make_obs(
        step=3,
        day=0,
        hour=3,
        farmer=(2, 2),
        hands=[[3, 3], [1, 1]],
        seeds={"WHEAT": 10},
    )
    act = agent(obs)

    assert "farmer" in act
    assert isinstance(act["farmer"], list)
    assert len(act["farmer"]) >= 1

    assert "hands" in act
    assert isinstance(act["hands"], list)
    assert len(act["hands"]) == 2
    for h_act in act["hands"]:
        assert isinstance(h_act, list)
        assert len(h_act) >= 1


def test_exception_fallback_returns_safe_pass() -> None:
    """If an internal exception occurs, agent returns safe PASS for all units."""
    obs = make_obs(step=5, day=0, hour=5, hands=[[1, 1]])

    with patch(
        "src.main.schedule_tasks", side_effect=RuntimeError("Simulated error")
    ):
        act = agent(obs)

    assert act["farmer"] == ["PASS"]
    assert act["hands"] == [["PASS"]]
    assert act["market"] == []


def test_exception_in_debug_mode_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """When JEREMY_DEBUG is enabled, unhandled exceptions raise rather than returning PASS."""
    monkeypatch.setenv("JEREMY_DEBUG", "1")
    obs = make_obs(step=5, day=0, hour=5, hands=[[1, 1]])

    with patch(
        "src.main.schedule_tasks", side_effect=RuntimeError("Simulated error")
    ):
        with pytest.raises(RuntimeError, match="Simulated error"):
            agent(obs)


def test_terminal_explosion_step_activates() -> None:
    """Terminal liquidation triggers when reaching explosion_step."""
    obs = make_obs(
        step=715,
        day=29,
        hour=19,
        shed={"MELON": 10},
        prices={"MELON": 250},
    )
    act = agent(obs)

    assert "farmer" in act
    assert "hands" in act
    assert "market" in act
    assert any(order[0] == "SELL" for order in act["market"])


def test_make_agent_closure_runs_turn() -> None:
    """make_agent factory produces a stateful closure that processes turns."""
    custom_agent = make_agent()
    obs = make_obs(step=0, day=0, hour=0, seeds={"WHEAT": 5})
    act = custom_agent(obs)

    assert "farmer" in act
    assert "hands" in act
    assert "market" in act


def test_simulation_run_episode_integration() -> None:
    """End-to-end headless simulation episode run with starter opponent."""
    from simulation.episode import run_episode

    res = run_episode(agent, "starter")
    assert res.replay_path is not None
    saved_file = Path(res.replay_path)
    assert saved_file.exists()
    assert res.score_challenger > 0
