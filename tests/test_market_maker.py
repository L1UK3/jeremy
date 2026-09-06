"""Unit tests for analytical supply projection and dynamic reservation pricing in market_maker."""

from __future__ import annotations

from typing import Any

from src.environment.board import Board
from src.environment.state import GameState
from src.strategies.market_maker import (
    PRICE_FLOOR,
    compute_analytical_supply,
    plan_sells,
    reserve_price,
)


def make_obs(
    step: int = 0,
    day: int = 0,
    money: int = 3000,
    shed: dict[str, int] | None = None,
    seeds: dict[str, int] | None = None,
    tiles: list[list[Any]] | None = None,
    unlocked_quadrants: list[str] | None = None,
) -> dict[str, Any]:
    """Helper to construct a realistic Kaggle observation dict."""
    if tiles is None:
        tiles = [[None for _ in range(10)] for _ in range(10)]
    quads = unlocked_quadrants or ["NW"]
    return {
        "player": 0,
        "step": step,
        "day": day,
        "hour": step % 24,
        "farms": [
            {
                "money": money,
                "tiles": tiles,
                "farmer": [2, 2],
                "hands": [],
                "unlocked_quadrants": quads,
                "hires_today": 0,
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
            "inventories": [[]],
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
            "prices": {
                "WHEAT": 25,
                "CARROT": 35,
                "TOMATO": 60,
                "STRAWBERRY": 120,
                "MELON": 250,
                "MILK": 160,
                "WOOL": 200,
            },
        },
        "town": {
            "unlocked_shops": ["BAKERY", "ICE_CREAM_SHOP"],
        },
    }


def test_analytical_supply_positive_and_decays() -> None:
    """Supply projection should be positive and decrease as season advances toward step 720."""
    tiles = [[None for _ in range(10)] for _ in range(10)]
    tiles[0][0] = {"kind": "PLANT", "crop": "MELON", "planted_day": 0, "watered_today": True, "yield_units": 2, "consecutive_unwatered": 0}
    tiles[0][1] = {"kind": "PLANT", "crop": "STRAWBERRY", "planted_day": 0, "watered_today": True, "yield_units": 2, "consecutive_unwatered": 0}
    tiles[0][2] = {"kind": "PLANT", "crop": "WHEAT", "planted_day": 0, "watered_today": True, "yield_units": 2, "consecutive_unwatered": 0}
    tiles[1][0] = {
        "kind": "PASTURE", "animal": "COW", "placed_day": 0, "yield_units": 1,
        "fed_today": True, "consecutive_unfed": 0, "cared_today": True,
        "fertilizer_available": False, "pending_care_bonus": 0,
    }
    tiles[1][1] = {
        "kind": "PASTURE", "animal": "SHEEP", "placed_day": 0, "yield_units": 1,
        "fed_today": True, "consecutive_unfed": 0, "cared_today": True,
        "fertilizer_available": False, "pending_care_bonus": 0,
    }

    obs_early = make_obs(step=24, day=1, tiles=tiles)
    state_early = GameState.from_obs(obs_early)
    board_early = Board(state_early)

    obs_late = make_obs(step=600, day=25, tiles=tiles)
    state_late = GameState.from_obs(obs_late)
    board_late = Board(state_late)

    for item in ("MELON", "STRAWBERRY", "MILK", "WOOL", "WHEAT"):
        supply_early = compute_analytical_supply(item, 24, state_early, board_early)
        supply_late = compute_analytical_supply(item, 600, state_late, board_late)

        assert supply_early > 0, f"Early supply for {item} must be positive"
        assert supply_early >= supply_late, f"Supply for {item} should decay from early ({supply_early}) to late ({supply_late})"


def test_analytical_supply_incorporates_active_board_yield_and_shed() -> None:
    """Standing crops and stored goods must augment projected supply."""
    tiles = [[None for _ in range(10)] for _ in range(10)]
    tiles[1][1] = {
        "kind": "PLANT",
        "crop": "MELON",
        "planted_day": 0,
        "watered_today": True,
        "yield_units": 5,
        "consecutive_unwatered": 0,
    }

    obs_empty = make_obs(step=100, day=4, shed={"MELON": 0})
    obs_loaded = make_obs(step=100, day=4, shed={"MELON": 10}, tiles=tiles)

    state_empty = GameState.from_obs(obs_empty)
    board_empty = Board(state_empty)

    state_loaded = GameState.from_obs(obs_loaded)
    board_loaded = Board(state_loaded)

    supply_empty = compute_analytical_supply("MELON", 100, state_empty, board_empty)
    supply_loaded = compute_analytical_supply("MELON", 100, state_loaded, board_loaded)

    assert supply_loaded > supply_empty
    # Difference should reflect at least the 10 shed items + 5 standing yield
    assert supply_loaded >= supply_empty + 15


def test_reserve_price_bounded_with_supply_projection() -> None:
    """reserve_price must produce sane, bounded prices across items."""
    obs = make_obs(step=48, day=2)
    state = GameState.from_obs(obs)
    board = Board(state)
    shops = ["BAKERY", "ICE_CREAM_SHOP"]

    for item in ("MELON", "STRAWBERRY", "MILK", "WOOL"):
        price = reserve_price(item, 48, state, board, shops, scale=1.0)
        assert price >= float(PRICE_FLOOR), f"Reservation price for {item} must be at least PRICE_FLOOR"
        assert price <= 300.0, f"Reservation price for {item} abnormally high: {price}"


def test_reserve_price_enforces_price_floor_at_terminal_steps() -> None:
    """reserve_price must never fall below PRICE_FLOOR, even in late terminal steps."""
    obs = make_obs(step=718, day=29)
    state = GameState.from_obs(obs)
    board = Board(state)
    shops = ["BAKERY"]

    for item in ("MELON", "STRAWBERRY", "WHEAT", "MILK"):
        price = reserve_price(item, 718, state, board, shops, scale=1.0)
        assert price >= float(PRICE_FLOOR), f"Price at step 718 for {item} must be at least {PRICE_FLOOR}"


def test_unlocked_quadrant_scales_active_crop_projection() -> None:
    """Expanding from 1 quadrant to 2 quadrants increases future capacity projection for active crops."""
    tiles = [[None for _ in range(10)] for _ in range(10)]
    tiles[0][0] = {"kind": "PLANT", "crop": "MELON", "planted_day": 0, "watered_today": True, "yield_units": 1, "consecutive_unwatered": 0}

    obs_nw = make_obs(step=100, day=4, tiles=tiles, unlocked_quadrants=["NW"])
    obs_nw_ne = make_obs(step=100, day=4, tiles=tiles, unlocked_quadrants=["NW", "NE"])

    state_nw = GameState.from_obs(obs_nw)
    board_nw = Board(state_nw)

    state_nw_ne = GameState.from_obs(obs_nw_ne)
    board_nw_ne = Board(state_nw_ne)

    supply_nw = compute_analytical_supply("MELON", 100, state_nw, board_nw)
    supply_nw_ne = compute_analytical_supply("MELON", 100, state_nw_ne, board_nw_ne)

    assert supply_nw_ne > supply_nw, "More unlocked quadrants should yield higher supply projection for active crops"


def test_zero_active_assets_returns_minimal_baseline() -> None:
    """When no crops, seeds, or animals exist, supply projection returns the floor without phantom projections."""
    obs_bare = make_obs(step=100, day=4)
    state_bare = GameState.from_obs(obs_bare)
    board_bare = Board(state_bare)

    # Bare farm has no melon plants, melon seeds, or melon in shed
    supply = compute_analytical_supply("MELON", 100, state_bare, board_bare)
    assert supply == float(PRICE_FLOOR), "Zero-asset commodity must equal PRICE_FLOOR (no phantom assets)"


def test_plan_sells_generates_orders_using_analytical_reserves() -> None:
    """plan_sells generates valid SELL orders for shed inventory when price exceeds reserve."""
    obs = make_obs(step=100, day=4, shed={"MELON": 3, "STRAWBERRY": 2})
    state = GameState.from_obs(obs)
    board = Board(state)

    orders = plan_sells(
        state,
        board,
        step=100,
        slots=5,
        short_of_cash=0.0,
        reservation_scales={"MELON": 1.0, "STRAWBERRY": 1.0},
    )
    assert len(orders) > 0
    items_sold = [o[1] for o in orders if o[0] == "SELL"]
    assert "MELON" in items_sold or "STRAWBERRY" in items_sold
