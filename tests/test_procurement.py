"""Unit tests for macro-driven procurement and selective land expansion."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from tests.conftest import EpisodeTrace

from src.environment.board import Board
from src.environment.state import GameState
from src.strategies.procurement import (
    ANIMAL_COSTS,
    DEFAULT_ACTIONS_PER_HAND,
    DEFAULT_EXPANSION_DAY_NE,
    DEFAULT_EXPANSION_DAY_SW,
    DEFAULT_LABOR_FLOOR,
    DEFAULT_LAND_COST_MULT,
    DEFAULT_LAND_MIN_CREW,
    DEFAULT_MAX_DAILY_HIRES,
    DEFAULT_MAX_HIRE_HOUR,
    LAND_COSTS,
    SEED_COSTS,
    apply_procurement,
    compute_quadrant_labor_floor,
    estimate_daily_action_demand,
    procure_crew,
    procure_feed,
    procure_land,
    procure_livestock,
    procure_seeds,
)


def make_obs(
    step: int = 0,
    day: int = 0,
    hour: int = 0,
    money: int = 3000,
    shed: dict[str, int] | None = None,
    seeds: dict[str, int] | None = None,
    tiles: list[list[Any]] | None = None,
    unlocked_quadrants: list[str] | None = None,
    hands: list[list[int]] | None = None,
    hires_today: int = 0,
    prices: dict[str, int] | None = None,
) -> dict[str, Any]:
    """Helper to construct a realistic Kaggle observation dict."""
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

    return {
        "player": 0,
        "step": step,
        "day": day,
        "hour": hour,
        "farms": [
            {
                "money": money,
                "tiles": tiles,
                "farmer": [2, 2],
                "hands": hands or [],
                "unlocked_quadrants": quads,
                "hires_today": hires_today,
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
            "prices": default_prices,
        },
        "town": {
            "unlocked_shops": ["BAKERY"],
        },
    }


# =========================================================================
# Default Constants & Optuna Configuration Tests
# =========================================================================


def test_procurement_default_constants() -> None:
    """Default hyperparameters match specification and provide baseline."""
    assert DEFAULT_LAND_COST_MULT == 2.0
    assert DEFAULT_LAND_MIN_CREW == 3
    assert DEFAULT_LABOR_FLOOR == 3
    assert DEFAULT_MAX_HIRE_HOUR == 2
    assert DEFAULT_EXPANSION_DAY_NE == 7
    assert DEFAULT_EXPANSION_DAY_SW == 11

    assert DEFAULT_ACTIONS_PER_HAND == 8.0
    assert DEFAULT_MAX_DAILY_HIRES == 10
    assert LAND_COSTS == {"NE": 1000, "SW": 2000}
    assert SEED_COSTS["WHEAT"] == 10
    assert ANIMAL_COSTS["COW"] == 400


# =========================================================================
# Land Expansion Tests
# =========================================================================


def test_procure_land_ne_quadrant_success() -> None:
    """NE land ($1,000) bought on Day >= 7 when money >= 2 * 1000."""
    obs = make_obs(day=7, money=2000, unlocked_quadrants=["NW"])
    state = GameState.from_obs(obs)
    market: list[list[Any]] = []

    rem = procure_land(market, state, target_crew=0)
    assert market == [["BUY_LAND"]]
    assert rem == 1000


def test_procure_land_ne_quadrant_fails_under_thresholds() -> None:
    """NE land is blocked if day < 7 or money < $2,000."""
    # Fails prior to Day 7
    obs_early = make_obs(day=6, money=3000, unlocked_quadrants=["NW"])
    state_early = GameState.from_obs(obs_early)
    market: list[list[Any]] = []
    procure_land(market, state_early)
    assert market == []

    # Fails if money < $2,000
    obs_low_money = make_obs(day=7, money=1999, unlocked_quadrants=["NW"])
    state_low_money = GameState.from_obs(obs_low_money)
    market.clear()
    procure_land(market, state_low_money)
    assert market == []


def test_procure_land_crew_restriction_removed() -> None:
    """target_crew < min_crew does NOT block land purchase when day and treasury met."""
    obs = make_obs(day=7, money=2000, unlocked_quadrants=["NW"])
    state = GameState.from_obs(obs)
    market: list[list[Any]] = []

    # target_crew=0 with min_crew=3 still purchases land
    procure_land(market, state, target_crew=0, min_crew=3)
    assert market == [["BUY_LAND"]]


def test_procure_land_sw_quadrant_success() -> None:
    """SW land bought when NE is unlocked, day >= 11, money >= 4000."""
    obs = make_obs(day=11, money=4000, unlocked_quadrants=["NW", "NE"])
    state = GameState.from_obs(obs)
    market: list[list[Any]] = []

    rem = procure_land(market, state, target_crew=0)
    assert market == [["BUY_LAND"]]
    assert rem == 2000


def test_procure_land_sw_quadrant_fails_under_thresholds() -> None:
    """SW land is blocked if day < 11 or money < $4,000."""
    # Fails prior to Day 11
    obs_early = make_obs(day=10, money=10000, unlocked_quadrants=["NW", "NE"])
    state_early = GameState.from_obs(obs_early)
    market: list[list[Any]] = []
    procure_land(market, state_early)
    assert market == []

    # Fails if money < $4,000
    obs_low_money = make_obs(
        day=11, money=3999, unlocked_quadrants=["NW", "NE"]
    )
    state_low_money = GameState.from_obs(obs_low_money)
    market.clear()
    procure_land(market, state_low_money)
    assert market == []



def test_procure_land_se_quadrant_never_purchased() -> None:
    """SE quadrant ($4,000) must NEVER be purchased under any circumstance."""
    obs = make_obs(day=20, money=20000, unlocked_quadrants=["NW", "NE", "SW"])
    state = GameState.from_obs(obs)
    market: list[list[Any]] = []

    procure_land(market, state, target_crew=10)
    assert market == []


def test_procure_land_duplicate_in_single_turn_prevented() -> None:
    """BUY_LAND is not queued if market already contains a BUY_LAND order."""
    obs = make_obs(day=6, money=5000, unlocked_quadrants=["NW"])
    state = GameState.from_obs(obs)
    market: list[list[Any]] = [["BUY_LAND"]]

    rem = procure_land(market, state)
    assert market == [["BUY_LAND"]]
    assert rem == 5000


def test_procure_land_parameterized_for_optuna() -> None:
    """procure_land supports custom cost_mult and day overrides for Optuna."""
    obs = make_obs(day=7, money=1500, unlocked_quadrants=["NW"])
    state = GameState.from_obs(obs)
    market: list[list[Any]] = []

    # Default cost_mult=2.0 requires $2000
    procure_land(market, state)
    assert market == []

    # Tuned parameters cost_mult=1.5 qualifies ($1500)
    procure_land(market, state, cost_mult=1.5)
    assert market == [["BUY_LAND"]]



# =========================================================================
# Crew Procurement Tests
# =========================================================================


def test_procure_crew_hires_up_to_target_in_early_hours() -> None:
    """Hands hired up to target_crew during hour <= 2 on Fibonacci costs."""
    obs = make_obs(hour=0, money=100, hands=[], hires_today=0)
    state = GameState.from_obs(obs)
    market: list[list[Any]] = []

    rem = procure_crew(market, state, target_crew=3)
    # Target crew 3: fib(0)=1, fib(1)=1, fib(2)=2 -> $4 spent
    assert market == [["HIRE"], ["HIRE"], ["HIRE"]]
    assert rem == 96


def test_procure_crew_skipped_past_max_hire_hour() -> None:
    """Hands are NOT hired when hour > max_hire_hour (default 2)."""
    obs = make_obs(hour=3, money=1000, hands=[], hires_today=0)
    state = GameState.from_obs(obs)
    market: list[list[Any]] = []

    procure_crew(market, state, target_crew=4)
    assert market == []


def test_procure_crew_max_hire_hour_override_for_optuna() -> None:
    """procure_crew supports custom max_hire_hour for Optuna tuning."""
    obs = make_obs(hour=5, money=100, hands=[], hires_today=0)
    state = GameState.from_obs(obs)
    market: list[list[Any]] = []

    procure_crew(market, state, target_crew=2)
    assert market == []

    procure_crew(market, state, target_crew=2, max_hire_hour=6)
    assert market == [["HIRE"], ["HIRE"]]


def test_procure_crew_respects_budget_limits() -> None:
    """Only affordable hires on the Fibonacci curve are queued."""
    obs = make_obs(hour=1, money=2, hands=[], hires_today=0)
    state = GameState.from_obs(obs)
    market: list[list[Any]] = []

    rem = procure_crew(market, state, target_crew=4)
    assert market == [["HIRE"], ["HIRE"]]
    assert rem == 0


def test_procure_crew_noop_when_crew_target_met() -> None:
    """No hires are issued if len(hands) >= target_crew."""
    obs = make_obs(hour=0, money=100, hands=[[1, 1], [1, 2]], hires_today=2)
    state = GameState.from_obs(obs)
    market: list[list[Any]] = []

    procure_crew(market, state, target_crew=2)
    assert market == []


def test_procure_crew_quadrant_labor_floor() -> None:
    """Labor floor ensures 2 hands for 1 quad, 4 hands for 2 quads, 6 hands for 3 quads."""
    assert compute_quadrant_labor_floor(1) == 2
    assert compute_quadrant_labor_floor(2) == 4
    assert compute_quadrant_labor_floor(3) == 6

    # 1 quadrant unlocked: floor is 2 hands even with target_crew=0
    obs_1 = make_obs(
        hour=0, money=100, hands=[], hires_today=0, unlocked_quadrants=["NW"]
    )
    state_1 = GameState.from_obs(obs_1)
    market_1: list[list[Any]] = []
    procure_crew(market_1, state_1, target_crew=0)
    assert len(market_1) == 2

    # 2 quadrants unlocked: floor is 4 hands even with target_crew=1
    obs_2 = make_obs(
        hour=0,
        money=100,
        hands=[],
        hires_today=0,
        unlocked_quadrants=["NW", "NE"],
    )
    state_2 = GameState.from_obs(obs_2)
    market_2: list[list[Any]] = []
    procure_crew(market_2, state_2, target_crew=1)
    assert len(market_2) == 4

    # 3 quadrants unlocked: floor is 6 hands
    obs_3 = make_obs(
        hour=0,
        money=100,
        hands=[],
        hires_today=0,
        unlocked_quadrants=["NW", "NE", "SW"],
    )
    state_3 = GameState.from_obs(obs_3)
    market_3: list[list[Any]] = []
    procure_crew(market_3, state_3, target_crew=0)
    assert len(market_3) == 6


def test_procure_crew_quadrant_floor_scales_with_pending_land() -> None:
    """Pending BUY_LAND order immediately elevates labor floor to staff the new quadrant."""
    obs = make_obs(
        hour=0, money=100, hands=[], hires_today=0, unlocked_quadrants=["NW"]
    )
    state = GameState.from_obs(obs)
    market: list[list[Any]] = [["BUY_LAND"]]

    procure_crew(market, state, target_crew=0)
    hire_orders = [o for o in market if o[0] == "HIRE"]
    assert len(hire_orders) == 4  # 1 current + 1 pending = 2 quads -> 4 hands


def test_procure_crew_neural_target_above_floor() -> None:
    """Neural policy target_crew can exceed deterministic quadrant floor."""
    obs = make_obs(
        hour=0, money=100, hands=[], hires_today=0, unlocked_quadrants=["NW"]
    )
    state = GameState.from_obs(obs)
    market: list[list[Any]] = []

    procure_crew(market, state, target_crew=5)
    assert len(market) == 5


def test_estimate_daily_action_demand_empty_quadrant() -> None:
    """Empty unlocked NW quadrant generates plant + water actions for 23 tiles."""
    obs = make_obs(unlocked_quadrants=["NW"])
    state = GameState.from_obs(obs)
    board = Board(state)

    demand = estimate_daily_action_demand(state, board)
    # 23 empty non-reserved tiles: 23 plant actions + 23 initial water actions = 46
    assert demand == 46


def test_estimate_daily_action_demand_active_crops() -> None:
    """Unwatered plants and ripe crops are counted in daily action demand."""
    tiles = [[None for _ in range(10)] for _ in range(10)]
    # 10 growing unwatered wheat crops in NW
    for y in (0, 1):
        for x in range(5):
            tiles[y][x] = {
                "kind": "PLANT",
                "crop": "WHEAT",
                "planted_day": 9,
                "watered_today": False,
                "consecutive_unwatered": 0,
                "yield_units": 1,
                "max_lifespan_step": 100,
            }
    # 5 ripe melons in row 2 of NW
    for x in range(5):
        tiles[2][x] = {
            "kind": "PLANT",
            "crop": "MELON",
            "planted_day": 0,
            "watered_today": False,
            "consecutive_unwatered": 0,
            "yield_units": 6,
            "max_lifespan_step": 288,
        }
    obs = make_obs(day=10, tiles=tiles, unlocked_quadrants=["NW"])
    state = GameState.from_obs(obs)
    board = Board(state)

    demand = estimate_daily_action_demand(state, board)
    # 15 unwatered plants = 15 water actions
    # 5 ripe melons = 5 harvest actions + ceil(5/3)=2 drop actions
    # Remaining empty non-reserved tiles in NW (25 - 2 reserved - 10 - 5 = 8 empty tiles)
    # 8 plant actions + 8 initial water actions = 16
    # Total: 15 + 5 + 2 + 16 = 38
    assert demand == 38


def test_procure_crew_scales_with_action_demand() -> None:
    """Action demand elevates crew hiring above the static quadrant floor."""
    obs = make_obs(
        hour=0, money=1000, hands=[], hires_today=0, unlocked_quadrants=["NW"]
    )
    state = GameState.from_obs(obs)
    board = Board(state)
    market: list[list[Any]] = []

    # 46 actions with actions_per_hand=8.0 -> ceil(46/8) = 6 units (1 farmer + 5 hands)
    procure_crew(
        market,
        state,
        target_crew=0,
        board=board,
        actions_per_hand=8.0,
    )
    assert len(market) == 5


def test_procure_crew_respects_max_daily_hires() -> None:
    """Daily hiring strictly caps at max_daily_hires even under extreme chore demand."""
    obs = make_obs(
        hour=0,
        money=50000,
        hands=[],
        hires_today=0,
        unlocked_quadrants=["NW", "NE", "SW"],
    )
    state = GameState.from_obs(obs)
    board = Board(state)
    market: list[list[Any]] = []

    # Extremely low actions_per_hand creating high crew demand
    procure_crew(
        market,
        state,
        target_crew=0,
        board=board,
        actions_per_hand=2.0,
        max_daily_hires=16,
    )
    assert len(market) <= 16


# =========================================================================
# Seed Procurement Tests
# =========================================================================


def test_procure_seeds_matches_empty_unlocked_tiles() -> None:
    """Procures target seeds to match empty tiles minus animal slots."""
    obs = make_obs(money=5000, unlocked_quadrants=["NW"], seeds={"MELON": 0})
    state = GameState.from_obs(obs)
    board = Board(state)
    market: list[list[Any]] = []

    procure_seeds(market, state, board, target_crop="MELON")
    assert market == [["BUY_SEED", "MELON", 23]]


def test_procure_seeds_accounts_for_held_seeds() -> None:
    """Does not buy seeds when held target seeds already satisfy demand."""
    obs = make_obs(money=5000, unlocked_quadrants=["NW"], seeds={"MELON": 23})
    state = GameState.from_obs(obs)
    board = Board(state)
    market: list[list[Any]] = []

    procure_seeds(market, state, board, target_crop="MELON")
    assert market == []


def test_procure_seeds_accounts_for_non_target_held_seeds() -> None:
    """Does not re-purchase seeds when non-target seeds cover empty tiles."""
    obs = make_obs(money=5000, unlocked_quadrants=["NW"], seeds={"WHEAT": 23})
    state = GameState.from_obs(obs)
    board = Board(state)
    market: list[list[Any]] = []

    procure_seeds(market, state, board, target_crop="MELON")
    assert market == []


def test_procure_seeds_deficit_calculation() -> None:
    """Buys only the deficit when partial seeds are held."""
    obs = make_obs(money=5000, unlocked_quadrants=["NW"], seeds={"MELON": 10})
    state = GameState.from_obs(obs)
    board = Board(state)
    market: list[list[Any]] = []

    procure_seeds(market, state, board, target_crop="MELON")
    assert market == [["BUY_SEED", "MELON", 13]]


def test_procure_seeds_wheat_fallback_on_budget_shortage() -> None:
    """Buys affordable target crop then falls back to WHEAT for remainder."""
    obs = make_obs(
        money=250, unlocked_quadrants=["NW"], seeds={"STRAWBERRY": 0}
    )
    state = GameState.from_obs(obs)
    board = Board(state)
    market: list[list[Any]] = []

    procure_seeds(market, state, board, target_crop="STRAWBERRY")
    assert market == [["BUY_SEED", "STRAWBERRY", 2], ["BUY_SEED", "WHEAT", 5]]


def test_procure_seeds_complete_wheat_fallback() -> None:
    """When target crop cannot be afforded, available budget buys WHEAT."""
    obs = make_obs(money=40, unlocked_quadrants=["NW"], seeds={"STRAWBERRY": 0})
    state = GameState.from_obs(obs)
    board = Board(state)
    market: list[list[Any]] = []

    procure_seeds(market, state, board, target_crop="STRAWBERRY")
    assert market == [["BUY_SEED", "WHEAT", 4]]


def test_procure_seeds_custom_reserved_tiles_for_optuna() -> None:
    """procure_seeds supports custom animal coordinates for Optuna."""
    obs = make_obs(money=5000, unlocked_quadrants=["NW"], seeds={"MELON": 0})
    state = GameState.from_obs(obs)
    board = Board(state)
    market: list[list[Any]] = []

    procure_seeds(
        market,
        state,
        board,
        target_crop="MELON",
        reserved_tiles={(3, 4)},
    )
    assert market == [["BUY_SEED", "MELON", 24]]


def test_procure_seeds_day_28_and_29_absolute_freeze() -> None:
    """Zero seed orders emitted on Days 28 and 29 regardless of budget or empty tiles."""
    for freeze_day in (28, 29):
        obs = make_obs(
            day=freeze_day,
            money=5000,
            unlocked_quadrants=["NW"],
            seeds={"WHEAT": 0},
        )
        state = GameState.from_obs(obs)
        board = Board(state)
        market: list[list[Any]] = []

        rem = procure_seeds(market, state, board, target_crop="WHEAT")
        assert market == [], f"Day {freeze_day} emitted seed orders: {market}"
        assert rem == 5000


def test_procure_seeds_maturation_horizon_melon_falls_back_to_wheat() -> None:
    """Target crop that cannot mature (MELON on Day 20) evaluates faster WHEAT alternative."""
    # MELON first_yield_day is 10. At Day 20, 20 + 10 = 30 >= 30, so MELON cannot yield.
    # WHEAT first_yield_day is 2. At Day 20, 20 + 2 = 22 < 30, so WHEAT matures before Day 30.
    obs = make_obs(
        day=20,
        money=5000,
        unlocked_quadrants=["NW"],
        seeds={"MELON": 0, "WHEAT": 0},
    )
    state = GameState.from_obs(obs)
    board = Board(state)
    market: list[list[Any]] = []

    procure_seeds(market, state, board, target_crop="MELON")
    assert market == [["BUY_SEED", "WHEAT", 23]]


def test_procure_seeds_crop_maturation_horizon_allows_viable_target() -> None:
    """Target crop that can mature (MELON on Day 19) is procured normally."""
    # At Day 19, 19 + 10 = 29 < 30, so MELON can yield before season end.
    obs = make_obs(
        day=19,
        money=5000,
        unlocked_quadrants=["NW"],
        seeds={"MELON": 0},
    )
    state = GameState.from_obs(obs)
    board = Board(state)
    market: list[list[Any]] = []

    procure_seeds(market, state, board, target_crop="MELON")
    assert market == [["BUY_SEED", "MELON", 23]]


def test_procure_seeds_capacity_limit_during_land_expansion() -> None:
    """Seed orders strictly respect empty unlocked tiles minus held and pre-queued seeds."""
    obs = make_obs(
        day=5,
        money=5000,
        unlocked_quadrants=["NW", "NE"],
        seeds={"WHEAT": 10},
    )
    state = GameState.from_obs(obs)
    board = Board(state)
    # Total empty unlocked tiles across NW (25) & NE (25) minus 4 animal plots: 50 - 4 = 46.
    # 10 seeds held, 6 already queued in market -> needed = 48 - 16 = 32.
    market: list[list[Any]] = [["BUY_SEED", "WHEAT", 6]]

    procure_seeds(market, state, board, target_crop="WHEAT")

    total_bought = sum(o[2] for o in market if o[0] == "BUY_SEED")
    assert total_bought + 10 <= 46
    assert market == [["BUY_SEED", "WHEAT", 6], ["BUY_SEED", "WHEAT", 30]]


# =========================================================================
# Livestock and Feed Tests
# =========================================================================


def test_procure_livestock_and_feed_when_selected() -> None:
    """Purchases wheat feed reserves and animal when selected with budget."""
    obs = make_obs(
        step=50,
        money=3000,
        shed={"WHEAT": 0},
        prices={"WHEAT": 25},
    )
    state = GameState.from_obs(obs)
    board = Board(state)
    market: list[list[Any]] = []

    procure_feed(market, state, n_animals=0, target_animal="COW")
    procure_livestock(
        market, state, target_animal="COW", animal_tiles=board.animals()
    )

    # Exact feed deficit is 2 units (reserve 2 - 0 held = 2)
    assert ["BUY_PRODUCT", "WHEAT", 2] in market
    assert ["BUY_ANIMAL", "COW", 1] in market


def test_procure_livestock_none_target_does_nothing() -> None:
    """When target_animal is NONE, no animal or extra feed orders placed."""
    obs = make_obs(step=50, money=3000, shed={"WHEAT": 0})
    state = GameState.from_obs(obs)
    board = Board(state)
    market: list[list[Any]] = []

    procure_feed(market, state, n_animals=0, target_animal="NONE")
    procure_livestock(
        market, state, target_animal="NONE", animal_tiles=board.animals()
    )
    assert market == []


def test_procure_livestock_waits_for_unplaced_animal_in_shed() -> None:
    """Does not purchase another animal if one is waiting in the shed."""
    obs = make_obs(step=50, money=3000, shed={"COW": 1, "WHEAT": 10})
    state = GameState.from_obs(obs)
    board = Board(state)
    market: list[list[Any]] = []

    procure_livestock(
        market, state, target_animal="COW", animal_tiles=board.animals()
    )
    assert market == []


# =========================================================================
# Integration & Shared Budget Tests
# =========================================================================


def test_apply_procurement_orchestrates_all_orders_within_market_cap() -> None:
    """apply_procurement executes operations within the 10 order cap."""
    obs = make_obs(
        step=169,
        day=7,
        hour=1,
        money=5000,
        unlocked_quadrants=["NW"],
        shed={"WHEAT": 0},
        seeds={"MELON": 0},
    )
    state = GameState.from_obs(obs)

    board = Board(state)
    market: list[list[Any]] = []

    apply_procurement(
        market,
        state,
        board,
        target_crop="MELON",
        target_animal="COW",
        target_crew=3,
    )

    assert len(market) <= 10
    ops = [order[0] for order in market]
    assert "HIRE" in ops
    assert "BUY_LAND" in ops
    assert "BUY_SEED" in ops
    assert "BUY_PRODUCT" in ops
    assert "BUY_ANIMAL" in ops


def test_apply_procurement_shared_budget_deduction() -> None:
    """Committed expenditures reduce budget for subsequent orders."""
    # Money = 2000. NE land costs 1000. HIRE 3 costs $4.
    # Total remaining for seeds is 2000 - 4 - 1000 = 996.
    # MELON costs $80. 23 tiles * 80 = 1840 > 996.
    # Seeds bought should be constrained by 996 budget, not 2000!
    obs = make_obs(
        step=168,
        day=7,
        hour=0,
        money=2000,
        unlocked_quadrants=["NW"],
        shed={"WHEAT": 0},
        seeds={"MELON": 0},
    )
    state = GameState.from_obs(obs)

    board = Board(state)
    market: list[list[Any]] = []

    rem_budget = apply_procurement(
        market,
        state,
        board,
        target_crop="MELON",
        target_animal="NONE",
        target_crew=3,
    )

    ops = [order[0] for order in market]
    assert "HIRE" in ops
    assert "BUY_LAND" in ops
    # Seed orders must fit in remaining budget without overdraft
    seed_orders = [o for o in market if o[0] == "BUY_SEED"]
    total_seed_spent = sum(
        qty * SEED_COSTS[crop] for _, crop, qty in seed_orders
    )
    assert total_seed_spent <= (2000 - 4 - 1000)
    assert rem_budget >= 0


def test_final_step_zero_unplanted_seeds(episode_trace: EpisodeTrace) -> None:
    """Final step inspection confirms 0 unplanted seeds in seeds inventory on Day 30."""
    seat = episode_trace.seat
    steps = episode_trace.steps
    final_step = steps[-1][seat]
    obs = final_step.get("observation") or {}
    priv = obs.get("private") or {}
    seeds = priv.get("seeds") or {}
    total_unplanted = sum(seeds.values())
    assert total_unplanted == 0, (
        f"Expected 0 unplanted seeds on Day 30, found {seeds}"
    )


def test_apply_procurement_prioritizes_feed_over_seeds() -> None:
    """Feed procurement must execute before seed procurement when budget is tight."""
    tiles: list[list[Any]] = [[None for _ in range(10)] for _ in range(10)]
    tiles[3][4] = {
        "kind": "PASTURE",
        "animal": "COW",
        "placed_day": 0,
        "yield_units": 0,
        "fed_today": False,
    }
    obs = make_obs(
        step=24,
        day=1,
        money=100,
        unlocked_quadrants=["NW"],
        tiles=tiles,
        shed={"WHEAT": 0},
    )
    state = GameState.from_obs(obs)
    board = Board(state)
    market: list[list[Any]] = []

    apply_procurement(
        market,
        state,
        board,
        target_crop="MELON",
        target_animal="NONE",
        target_crew=0,
    )

    feed_indices = [
        i
        for i, o in enumerate(market)
        if o[0] == "BUY_PRODUCT" and o[1] == "WHEAT"
    ]
    seed_indices = [i for i, o in enumerate(market) if o[0] == "BUY_SEED"]

    assert len(feed_indices) > 0, "Feed order must be emitted for active cow"
    if seed_indices:
        assert (
            feed_indices[0] < seed_indices[0]
        ), "Feed must be ordered before seeds"


def test_procure_seeds_day_zero_wheat_anchor() -> None:
    """On Day 0, apply_procurement must order at least 6 wheat seeds alongside cash crops."""
    obs = make_obs(
        step=0,
        day=0,
        money=3000,
        unlocked_quadrants=["NW"],
        shed={"WHEAT": 0},
        seeds={},
    )
    state = GameState.from_obs(obs)
    board = Board(state)
    market: list[list[Any]] = []

    apply_procurement(
        market,
        state,
        board,
        target_crop="MELON",
        target_animal="NONE",
        target_crew=0,
    )

    wheat_orders = [
        o[2] for o in market if o[0] == "BUY_SEED" and o[1] == "WHEAT"
    ]
    assert sum(wheat_orders) >= 6, (
        "Must procure at least 6 wheat seeds on Day 0"
    )


def test_mid_game_strawberry_default() -> None:
    """Between Days 8 and 22, procure_seeds defaults empty tiles to STRAWBERRY."""
    obs = make_obs(
        step=240,
        day=10,
        money=5000,
        unlocked_quadrants=["NW", "NE"],
        seeds={},
    )
    state = GameState.from_obs(obs)
    board = Board(state)
    market: list[list[Any]] = []

    procure_seeds(market, state, board, target_crop="CARROT")
    strawberry_orders = [
        o[2] for o in market if o[0] == "BUY_SEED" and o[1] == "STRAWBERRY"
    ]
    assert sum(strawberry_orders) > 0, (
        "Must buy STRAWBERRY on Day 10 instead of CARROT"
    )


def test_strawberry_labor_scaling() -> None:
    """During mid-game with multiple quadrants, procure_crew provisions at least 8 hands."""
    obs = make_obs(
        step=300,
        day=12,
        hour=0,
        money=5000,
        hands=[],
        hires_today=0,
        unlocked_quadrants=["NW", "NE"],
    )
    state = GameState.from_obs(obs)
    board = Board(state)
    market: list[list[Any]] = []

    procure_crew(market, state, target_crew=0, board=board)
    hires = sum(1 for o in market if o[0] == "HIRE")
    assert hires >= 8, (
        f"Expected at least 8 hires for 2 quadrants on Day 12, got {hires}"
    )



