from __future__ import annotations

from economics.evaluators import (
    BYPRODUCTS,
    MAX_MARKET_ORDERS,
    evaluate_expansion,
    evaluate_livestock,
    evaluate_market,
    is_expansion_stage_allowed,
)
from economics.market import Market
from environment.board import Board
from environment.state import GameState


def _base_obs(
    step: int = 0,
    money: int = 3000,
    unlocked_quadrants: list[str] | None = None,
    farmer: list[int] | None = None,
    tiles: list[list[dict | None]] | None = None,
    shed: dict | None = None,
    seeds: dict | None = None,
    prices: dict | None = None,
) -> dict:
    if unlocked_quadrants is None:
        unlocked_quadrants = ["NW"]
    if farmer is None:
        farmer = [4, 4]
    if tiles is None:
        tiles = [[None for _ in range(10)] for _ in range(10)]
    if shed is None:
        shed = {}
    if seeds is None:
        seeds = {}
    if prices is None:
        prices = {
            "WHEAT": 25,
            "CARROT": 35,
            "MELON": 250,
            "MILK": 100,
            "WOOL": 150,
            "EGG": 50,
            "FERTILIZER": 30,
        }

    return {
        "player": 0,
        "step": step,
        "day": step // 24,
        "hour": step % 24,
        "market": {"prices": prices},
        "farms": [
            {
                "money": money,
                "farmer": farmer,
                "hands": [],
                "unlocked_quadrants": unlocked_quadrants,
                "tiles": tiles,
            }
        ],
        "private": {"shed": shed, "seeds": seeds},
    }


# =========================================================================
# Expansion Evaluator Tests
# =========================================================================


def test_is_expansion_stage_allowed():
    # 1 quadrant unlocked
    assert (
        is_expansion_stage_allowed(day=5, num_unlocked=1, money=5000) is False
    )
    assert is_expansion_stage_allowed(day=8, num_unlocked=1, money=5000) is True

    # 2 quadrants unlocked
    assert (
        is_expansion_stage_allowed(day=15, num_unlocked=2, money=8000) is False
    )
    assert (
        is_expansion_stage_allowed(day=22, num_unlocked=2, money=8000) is True
    )
    assert (
        is_expansion_stage_allowed(day=25, num_unlocked=2, money=1000) is False
    )

    # 3+ quadrants unlocked
    assert (
        is_expansion_stage_allowed(day=25, num_unlocked=3, money=10000) is False
    )


def test_evaluate_expansion_disabled():
    obs = _base_obs(step=200, money=5000)
    state = GameState.from_obs(obs)

    assert evaluate_expansion(state, expand_land=False) is None


def test_evaluate_expansion_day_constraints():
    # Day 5 (< 8): Cannot expand to 2nd quadrant even with sufficient funds
    obs_early = _base_obs(step=5 * 24, money=5000)
    state_early = GameState.from_obs(obs_early)

    assert evaluate_expansion(state_early) is None

    # Day 8 (>= 8): Can expand to 2nd quadrant (NE)
    obs_day8 = _base_obs(step=8 * 24, money=5000)
    state_day8 = GameState.from_obs(obs_day8)

    order = evaluate_expansion(state_day8)
    assert order is not None
    assert order == ["BUY_LAND", 5, 0]


def test_evaluate_expansion_third_quadrant():
    # Day 15 (< 22): Cannot expand to 3rd quadrant
    obs_mid = _base_obs(
        step=15 * 24,
        money=8000,
        unlocked_quadrants=["NW", "NE"],
    )
    state_mid = GameState.from_obs(obs_mid)

    assert evaluate_expansion(state_mid) is None

    # Day 22 (>= 22): Can expand to 3rd quadrant (SW)
    obs_day22 = _base_obs(
        step=22 * 24,
        money=8000,
        unlocked_quadrants=["NW", "NE"],
    )
    state_day22 = GameState.from_obs(obs_day22)

    order = evaluate_expansion(state_day22)
    assert order is not None
    assert order == ["BUY_LAND", 0, 5]


def test_evaluate_expansion_max_reached():
    # Already has 3 quadrants (NW, NE, SW)
    obs_full = _base_obs(
        step=25 * 24,
        money=10000,
        unlocked_quadrants=["NW", "NE", "SW"],
    )
    state_full = GameState.from_obs(obs_full)

    assert evaluate_expansion(state_full) is None


# =========================================================================
# Livestock Evaluator Tests
# =========================================================================


def test_evaluate_livestock_no_animals():
    obs = _base_obs()
    state = GameState.from_obs(obs)
    board = Board(state)

    assert evaluate_livestock(state, board) is None


def test_evaluate_livestock_tile_actions():
    # 1. Animal tile with yield > 0 -> HARVEST
    tiles = [[None for _ in range(10)] for _ in range(10)]
    tiles[4][4] = {
        "kind": "PASTURE",
        "animal": "COW",
        "yield_units": 2,
        "fed_today": True,
        "cared_today": True,
        "fertilizer_available": False,
        "consecutive_unfed": 0,
    }
    obs = _base_obs(farmer=[4, 4], tiles=tiles)
    state = GameState.from_obs(obs)
    board = Board(state)
    assert evaluate_livestock(state, board) == ["HARVEST"]

    # 2. Animal tile with fertilizer available -> COLLECT_FERTILIZER
    tiles[4][4] = {
        "kind": "PASTURE",
        "animal": "COW",
        "yield_units": 0,
        "fed_today": True,
        "cared_today": True,
        "fertilizer_available": True,
        "consecutive_unfed": 0,
    }
    obs = _base_obs(farmer=[4, 4], tiles=tiles)
    state = GameState.from_obs(obs)
    board = Board(state)
    assert evaluate_livestock(state, board) == ["COLLECT_FERTILIZER"]

    # 3. Animal tile not cared today -> CARE
    tiles[4][4] = {
        "kind": "PASTURE",
        "animal": "COW",
        "yield_units": 0,
        "fed_today": True,
        "cared_today": False,
        "fertilizer_available": False,
        "consecutive_unfed": 0,
    }
    obs = _base_obs(farmer=[4, 4], tiles=tiles)
    state = GameState.from_obs(obs)
    board = Board(state)
    assert evaluate_livestock(state, board) == ["CARE"]


def test_evaluate_livestock_pickup_and_feed():
    tiles = [[None for _ in range(10)] for _ in range(10)]
    tiles[0][0] = {
        "kind": "PASTURE",
        "animal": "COW",
        "yield_units": 0,
        "fed_today": False,
        "cared_today": True,
        "fertilizer_available": False,
        "consecutive_unfed": 0,
    }
    # Farmer at shed (4, 4) with wheat in shed
    obs = _base_obs(farmer=[4, 4], tiles=tiles, shed={"WHEAT": 5})
    state = GameState.from_obs(obs)
    board = Board(state)

    act = evaluate_livestock(state, board)
    assert act is not None
    assert act[0] == "PICKUP"
    assert act[1] == "WHEAT"
    assert isinstance(act[2], int)
    assert act[2] == 1


# =========================================================================
# Market Evaluator Tests
# =========================================================================


def test_evaluate_market_feed_purchasing():
    # 2 cows, 0 wheat in shed -> should prioritize buying wheat
    tiles = [[None for _ in range(10)] for _ in range(10)]
    tiles[0][0] = {
        "kind": "PASTURE",
        "animal": "COW",
        "yield_units": 0,
        "fed_today": False,
        "cared_today": True,
        "fertilizer_available": False,
        "consecutive_unfed": 0,
    }
    tiles[0][1] = {
        "kind": "PASTURE",
        "animal": "SHEEP",
        "yield_units": 0,
        "fed_today": False,
        "cared_today": True,
        "fertilizer_available": False,
        "consecutive_unfed": 0,
    }
    obs = _base_obs(money=2000, tiles=tiles, shed={"WHEAT": 0})
    state = GameState.from_obs(obs)
    board = Board(state)
    market = Market(state)

    orders = evaluate_market(state, board, market, crop="WHEAT")
    assert len(orders) <= MAX_MARKET_ORDERS
    assert any(
        order[0] == "BUY_PRODUCT" and order[1] == "WHEAT" for order in orders
    )


def test_evaluate_market_selling_and_hiring():
    obs = _base_obs(
        money=5000,
        shed={"MILK": 10, "WOOL": 10, "FERTILIZER": 10, "MELON": 20},
    )
    state = GameState.from_obs(obs)
    board = Board(state)
    market = Market(state)

    orders = evaluate_market(state, board, market, crop="WHEAT")
    assert len(orders) <= MAX_MARKET_ORDERS
    # Should include sell orders for high value byproducts
    assert any(
        order[0] == "SELL" and order[1] in BYPRODUCTS for order in orders
    )
    # Should include hiring orders given large budget
    assert any(order[0] == "HIRE" for order in orders)


def test_evaluate_empty_pasture_animal_flow():
    # Empty pasture at (0, 0)
    tiles = [[None for _ in range(10)] for _ in range(10)]
    tiles[0][0] = {"kind": "PASTURE"}  # Empty pasture
    obs = _base_obs(money=2000, tiles=tiles, shed={"SHEEP": 0, "WHEAT": 10})
    state = GameState.from_obs(obs)
    board = Board(state)
    market = Market(state)

    orders = evaluate_market(state, board, market, crop="WHEAT")
    # Should buy animal when empty pasture exists
    assert any(order[0] == "BUY_ANIMAL" for order in orders)

    # Worker holding animal at (0, 0) should PLACE
    obs_place = _base_obs(
        farmer=[0, 0],
        tiles=tiles,
    )
    obs_place["private"]["inventories"] = [{"SHEEP": 1}]
    state_place = GameState.from_obs(obs_place)
    board_place = Board(state_place)
    act = evaluate_livestock(state_place, board_place, worker_idx=0)
    assert act == ["PLACE", "SHEEP"]
