from __future__ import annotations

from typing import TYPE_CHECKING, Any

from economics.economy import (
    affordable_hires,
    next_quadrant_target,
    should_buy_seed,
    should_expand,
)
from environment.board import Board, step_toward
from environment.state import GameState

if TYPE_CHECKING:
    from economics.market import Market
    from environment.board import Tile

__all__ = [
    "ANIMAL_FEED_BUFFER_DAYS",
    "BYPRODUCTS",
    "DEFAULT_SEED_TARGET",
    "EMERGENCY_FEED_RESERVE",
    "EXPEDITE_LIQUIDATION_DAY",
    "HIGH_VALUE_BYPRODUCTS",
    "MAX_HIRES_PER_BATCH",
    "MAX_MARKET_ORDERS",
    "MAX_TRANSACTION_QUANTITY",
    "SHED_HIGH_CAPACITY_THRESHOLD",
    "evaluate_expansion",
    "evaluate_livestock",
    "evaluate_market",
    "is_expansion_stage_allowed",
]

# Market Configuration Constants
MAX_MARKET_ORDERS: int = 10
MAX_HIRES_PER_BATCH: int = 8
MAX_TRANSACTION_QUANTITY: int = 10
ANIMAL_FEED_BUFFER_DAYS: int = 3
EMERGENCY_FEED_RESERVE: int = 100
SHED_HIGH_CAPACITY_THRESHOLD: int = 50
EXPEDITE_LIQUIDATION_DAY: int = 26
DEFAULT_SEED_TARGET: int = 12
HIGH_VALUE_BYPRODUCTS: tuple[str, ...] = (
    "MILK",
    "WOOL",
    "EGG",
    "FERTILIZER",
    "MELON",
    "WHEAT",
    "CARROT",
)
BYPRODUCTS: tuple[str, ...] = ("FERTILIZER", "MILK", "WOOL", "EGG")


def is_expansion_stage_allowed(
    day: int, num_unlocked: int, money: int = 0, max_limit: int = 3
) -> bool:
    """Determine whether land expansion is allowed based on day, unlocked quadrants and capital."""
    if num_unlocked >= max_limit:
        return False
    if num_unlocked == 1 and day < 8:
        return False
    if num_unlocked == 2 and (day < 22 or money < 3000):
        return False
    if num_unlocked >= 3:
        return False
    return True


def evaluate_expansion(
    state: GameState,
    expand_land: bool = True,
) -> list[str | int] | None:
    """Evaluate land expansion orders based on day, unlocked quadrants, and economy."""
    if not expand_land:
        return None

    num_unlocked = len(state.unlocked_quadrants_set)

    if not is_expansion_stage_allowed(state.day, num_unlocked, state.money):
        return None

    if not should_expand(state):
        return None

    if target := next_quadrant_target(state):
        return ["BUY_LAND", target[0], target[1]]

    return None


def _livestock_tile_action(
    tile: Tile | None, carried_wheat: int
) -> list[str | int] | None:
    """Execute immediate interaction on the current animal tile underfoot."""
    if not tile or not tile.is_animal:
        return None

    # Feed hungry animal if worker is holding feed
    if not tile.fed_today and carried_wheat > 0:
        return ["FEED"]

    # Daily grooming and care
    if not tile.cared_today:
        return ["CARE"]

    # Collect available byproduct fertilizer
    if tile.fertilizer_available:
        return ["COLLECT_FERTILIZER"]

    # Harvest mature animal products (wool, milk, egg)
    if tile.yield_units > 0:
        return ["HARVEST"]

    return None


def _livestock_feed_pickup(
    state: GameState,
    board: Board,
    fx: int,
    fy: int,
    needs_feed_count: int,
    carried_wheat: int,
) -> list[str | int] | None:
    """Evaluate shed navigation and wheat pickup when worker is empty-handed."""
    if needs_feed_count == 0 or carried_wheat > 0:
        return None

    shed_wheat = state.inventory("WHEAT")
    if shed_wheat <= 0:
        return None

    if state.is_shed_adjacent(fx, fy):
        pickup_qty = min(needs_feed_count, shed_wheat)
        return ["PICKUP", "WHEAT", pickup_qty]

    target_shed = board.nearest_shed(fx, fy)
    return [step_toward(fx, fy, target_shed[0], target_shed[1])]


def _livestock_chore_navigation(
    board: Board, fx: int, fy: int, carried_wheat: int
) -> list[str | int] | None:
    """Select highest-priority chore target and compute directional navigation step."""
    needs_feed = board.needs_feed()
    urgent_feed = [t for t in needs_feed if t.consecutive_unfed >= 1]
    needs_care = board.needs_care()
    needs_fert = board.has_fertilizer_tiles()
    needs_prod_harvest = [t for t in board.animals() if t.yield_units > 0]

    if needs_feed and carried_wheat > 0:
        target = board.nearest_to(
            fx, fy, urgent_feed if urgent_feed else needs_feed
        )
        if target:
            return [step_toward(fx, fy, target.x, target.y)]

    if needs_care:
        target = board.nearest_to(fx, fy, needs_care)
        if target:
            return [step_toward(fx, fy, target.x, target.y)]

    if needs_fert:
        target = board.nearest_to(fx, fy, needs_fert)
        if target:
            return [step_toward(fx, fy, target.x, target.y)]

    if needs_prod_harvest:
        target = board.nearest_to(fx, fy, needs_prod_harvest)
        if target:
            return [step_toward(fx, fy, target.x, target.y)]

    return None


def _livestock_byproduct_drop(
    state: GameState, board: Board, fx: int, fy: int, has_byproducts: bool
) -> list[str | int] | None:
    """Evaluate shed navigation and byproduct deposit when carrying harvested goods."""
    if not has_byproducts:
        return None

    if state.is_shed_adjacent(fx, fy):
        return ["DROP"]

    target_shed = board.nearest_shed(fx, fy)
    return [step_toward(fx, fy, target_shed[0], target_shed[1])]


def _livestock_placement_action(
    state: GameState,
    board: Board,
    fx: int,
    fy: int,
    worker_idx: int,
) -> list[str | int] | None:
    """Evaluate placing an animal in an empty pasture or picking one up from shed."""
    inv = state.worker_inventory(worker_idx)
    holding_animal = None
    for a in ("SHEEP", "COW", "GOOSE"):
        if inv.get(a, 0) > 0:
            holding_animal = a
            break

    empty_pastures = board.empty_pastures()
    if not empty_pastures and not holding_animal:
        return None

    current_tile = board.tile(fx, fy)
    if holding_animal:
        if current_tile and current_tile.empty_pasture:
            return ["PLACE", holding_animal]
        if empty_pastures:
            target = board.nearest_to(fx, fy, empty_pastures)
            if target:
                return [step_toward(fx, fy, target.x, target.y)]
        return None

    animals_in_shed = [
        a for a in ("SHEEP", "COW", "GOOSE") if state.inventory(a) > 0
    ]
    if empty_pastures and animals_in_shed:
        a_type = animals_in_shed[0]
        if state.is_shed_adjacent(fx, fy):
            pickup_qty = min(len(empty_pastures), state.inventory(a_type))
            return ["PICKUP", a_type, pickup_qty]
        target_shed = board.nearest_shed(fx, fy)
        return [step_toward(fx, fy, target_shed[0], target_shed[1])]

    return None


def evaluate_livestock(
    state: GameState,
    board: Board,
    worker_idx: int = 0,
    worker_pos: tuple[int, int] | None = None,
) -> list[str | int] | None:
    """Evaluate livestock management actions for a given worker."""
    if not board.animals() and not board.empty_pastures():
        return None

    fx, fy = worker_pos if worker_pos is not None else state.farmer
    inv = state.worker_inventory(worker_idx)
    carried_wheat = inv.get("WHEAT", 0)
    has_byproducts = any(inv.get(p, 0) > 0 for p in BYPRODUCTS)

    # Empty pasture animal placement
    if place_act := _livestock_placement_action(
        state, board, fx, fy, worker_idx
    ):
        return place_act

    # Immediate interaction on current tile underfoot
    current_tile = board.tile(fx, fy)
    if tile_act := _livestock_tile_action(current_tile, carried_wheat):
        return tile_act

    # Feed pickup from shed if empty-handed
    needs_feed = board.needs_feed()
    if pickup_act := _livestock_feed_pickup(
        state, board, fx, fy, len(needs_feed), carried_wheat
    ):
        return pickup_act

    # Navigation to active chore target
    if nav_act := _livestock_chore_navigation(board, fx, fy, carried_wheat):
        return nav_act

    # Byproduct return & shed deposit
    if drop_act := _livestock_byproduct_drop(
        state, board, fx, fy, has_byproducts
    ):
        return drop_act

    return None


def _evaluate_animal_purchases(
    state: GameState, board: Board, quota: int
) -> list[list[Any]]:
    """Evaluate purchasing animals to populate any empty pasture/coop tiles."""
    if quota <= 0:
        return []

    empty_pastures = board.empty_pastures()
    if not empty_pastures:
        return []

    if state.money < 1000:
        return []

    needed = len(empty_pastures)
    animals_in_shed = sum(state.inventory(a) for a in ("SHEEP", "COW", "GOOSE"))
    to_buy = max(0, needed - animals_in_shed)
    if to_buy <= 0:
        return []

    buy_qty = min(quota, to_buy)
    return [["BUY_ANIMAL", "SHEEP", buy_qty]]


def _evaluate_feed_purchases(
    state: GameState, board: Board, quota: int
) -> list[list[Any]]:
    """Evaluate emergency animal feed purchases to maintain buffer."""
    if quota <= 0:
        return []

    animals = board.animals()
    if not animals:
        return []

    wheat_stock = state.inventory("WHEAT")
    needed = max(0, (len(animals) * ANIMAL_FEED_BUFFER_DAYS) - wheat_stock)
    if needed <= 0:
        return []

    price = max(1, state.price("WHEAT"))
    max_can_buy = min(needed, int(state.money // price))
    if max_can_buy > 0:
        buy_amt = min(MAX_TRANSACTION_QUANTITY, max_can_buy)
        return [["BUY_PRODUCT", "WHEAT", buy_amt]]

    return []


def _evaluate_farmhand_hiring(
    state: GameState,
    board: Board,
    quota: int,
) -> list[list[Any]]:
    """Evaluate farmhand hiring orders up to daily limit and budget reserves."""
    if quota <= 0:
        return []

    animals = board.animals()
    feed_deficit = (
        max(0, len(animals) - state.inventory("WHEAT")) if animals else 0
    )
    budget = (
        state.money - EMERGENCY_FEED_RESERVE
        if (feed_deficit > 0 and state.money > EMERGENCY_FEED_RESERVE)
        else (state.money if feed_deficit == 0 else 0)
    )
    if budget <= 0:
        return []

    count = affordable_hires(state, max_budget=budget)
    hire_orders: list[list[Any]] = []
    for _ in range(min(MAX_HIRES_PER_BATCH, quota, count)):
        hire_orders.append(["HIRE"])

    return hire_orders


def _is_produce_sellable(
    item: str,
    sellable_qty: int,
    cur_price: int,
    score: float,
    day: int,
    shed_total: int,
) -> bool:
    """Determine whether a produce item meets market liquidation criteria."""
    if sellable_qty <= 0:
        return False
    if day >= EXPEDITE_LIQUIDATION_DAY:
        return True
    if shed_total >= SHED_HIGH_CAPACITY_THRESHOLD:
        return True
    if item in HIGH_VALUE_BYPRODUCTS:
        return True
    if item == "MELON" and (
        cur_price >= 160 or score >= 200 or sellable_qty >= 15
    ):
        return True
    if cur_price >= 80:
        return True
    return False


def _evaluate_produce_selling(
    state: GameState,
    market: Market,
    animals_count: int,
    quota: int,
) -> list[list[Any]]:
    """Evaluate produce and byproduct liquidation orders."""
    if quota <= 0:
        return []

    sell_orders: list[list[Any]] = []
    shed_total = sum(state.shed.values())

    for item, count in state.shed.items():
        if len(sell_orders) >= quota:
            break
        if not count or count <= 0 or item in ("seed", "fertilizer_seed"):
            continue

        if item == "WHEAT" and animals_count > 0:
            sellable = max(0, count - (animals_count * ANIMAL_FEED_BUFFER_DAYS))
        else:
            sellable = count

        cur_price = state.price(item)
        score = market.sell_score(item)

        if _is_produce_sellable(
            item, sellable, cur_price, score, state.day, shed_total
        ):
            batch_size = min(MAX_TRANSACTION_QUANTITY, sellable)
            sell_orders.append(["SELL", item, batch_size])

    return sell_orders


def _evaluate_seed_purchases(
    state: GameState,
    board: Board,
    crop: str | None,
    quota: int,
) -> list[list[Any]]:
    """Evaluate seed restocking orders for active focus crop."""
    if quota <= 0 or not crop:
        return []

    empty_tiles = board.empty_tiles_count
    target = min(DEFAULT_SEED_TARGET, empty_tiles)
    if should_buy_seed(state, crop, target):
        qty = target - state.seed_count(crop)
        if qty > 0:
            return [["BUY_SEED", crop, qty]]

    return []


def evaluate_market(
    state: GameState,
    board: Board,
    market: Market,
    crop: str | None,
) -> list[list[Any]]:
    """Evaluate market orders for feed, animals, farmhands, produce, and seeds."""
    orders: list[list[Any]] = []

    orders.extend(
        _evaluate_feed_purchases(state, board, MAX_MARKET_ORDERS - len(orders))
    )
    orders.extend(
        _evaluate_animal_purchases(
            state, board, MAX_MARKET_ORDERS - len(orders)
        )
    )
    orders.extend(
        _evaluate_farmhand_hiring(state, board, MAX_MARKET_ORDERS - len(orders))
    )
    orders.extend(
        _evaluate_produce_selling(
            state, market, len(board.animals()), MAX_MARKET_ORDERS - len(orders)
        )
    )
    orders.extend(
        _evaluate_seed_purchases(
            state, board, crop, MAX_MARKET_ORDERS - len(orders)
        )
    )

    return orders[:MAX_MARKET_ORDERS]
