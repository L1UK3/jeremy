from __future__ import annotations

from typing import Any

from board import Board, step_toward
from controller import AgentController
from economy import Economy
from market import Market
from state import GameState

__all__ = ["evaluate_expansion", "evaluate_livestock", "evaluate_market"]

BYPRODUCTS: tuple[str, ...] = ("FERTILIZER", "MILK", "WOOL", "EGG")


def evaluate_livestock(
    state: GameState,
    board: Board,
    worker_idx: int = 0,
    worker_pos: tuple[int, int] | None = None,
) -> list[str] | None:
    """Execute complete livestock care chore routine (pickup wheat -> feed -> care -> collect -> drop)."""
    animals = board.animals()
    if not animals:
        return None

    fx, fy = worker_pos if worker_pos is not None else state.farmer
    inv = state.worker_inventory(worker_idx)
    carried_wheat = inv.get("WHEAT", 0)
    has_byproducts = any(inv.get(p, 0) > 0 for p in BYPRODUCTS)

    needs_feed = board.needs_feed()
    urgent_feed = [t for t in needs_feed if t.consecutive_unfed >= 1]
    needs_care = board.needs_care()
    needs_fert = board.has_fertilizer_tiles()
    needs_prod_harvest = [t for t in animals if t.yield_units > 0]

    current_tile = board.tile(fx, fy)
    if current_tile and current_tile.is_animal:
        if not current_tile.fed_today and carried_wheat > 0:
            return ["FEED"]
        if not current_tile.cared_today:
            return ["CARE"]
        if current_tile.fertilizer_available:
            return ["COLLECT_FERTILIZER"]
        if current_tile.yield_units > 0:
            return ["HARVEST"]

    if needs_feed and carried_wheat == 0:
        shed_wheat = state.inventory("WHEAT")
        if shed_wheat > 0:
            if state.is_shed_adjacent(fx, fy):
                pickup_qty = min(len(needs_feed), shed_wheat)
                return ["PICKUP", "WHEAT", str(pickup_qty)]
            target_shed = board.nearest_shed(fx, fy)
            return [step_toward(fx, fy, target_shed[0], target_shed[1])]

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

    if has_byproducts:
        if state.is_shed_adjacent(fx, fy):
            return ["DROP"]
        target_shed = board.nearest_shed(fx, fy)
        return [step_toward(fx, fy, target_shed[0], target_shed[1])]

    return None


def evaluate_expansion(
    state: GameState,
    eco: Economy,
    controller: AgentController,
) -> list[Any] | None:
    """Evaluate purchasing adjacent land quadrants."""
    if not controller.expand_land:
        return None

    num_unlocked = len(state.unlocked_quadrants_set)
    max_quads = controller.get_max_quadrants(state)

    if num_unlocked >= max_quads:
        return None

    if num_unlocked == 1:
        if state.day < 8:
            return None
        if not eco.should_expand():
            return None

    elif num_unlocked == 2:
        if state.day < 22:
            return None
        if not eco.should_expand():
            return None

    else:
        return None

    if target := eco.next_quadrant_target():
        return ["BUY_LAND", target[0], target[1]]

    return None


def evaluate_market(
    state: GameState,
    board: Board,
    eco: Economy,
    market: Market,
    controller: AgentController,
    crop: str | None,
) -> list[list[Any]]:
    """Evaluate market sell orders, seed purchases, worker hiring, and feed."""
    market_orders: list[list[Any]] = []
    animals = board.animals()

    # Animal Feed Purchasing (Priority 1)
    if animals:
        wheat_stock = state.inventory("WHEAT")
        needed = max(0, len(animals) * 3 - wheat_stock)
        if needed > 0:
            price = max(1, state.price("WHEAT"))
            max_can_buy = min(needed, int(state.money // price))
            if max_can_buy > 0:
                buy_amt = min(10, max_can_buy)
                market_orders.append(["BUY_PRODUCT", "WHEAT", buy_amt])

    # Farmhand Hiring
    max_hires = controller.get_max_hires(state)
    feed_deficit = (
        max(0, len(animals) - state.inventory("WHEAT")) if animals else 0
    )
    budget = (
        state.money - 100
        if (feed_deficit > 0 and state.money > 100)
        else (state.money if feed_deficit == 0 else 0)
    )
    if budget > 0:
        count = eco.affordable_hires(
            max_hires_per_day=max_hires, max_budget=budget
        )
        for _ in range(min(8, count)):
            if len(market_orders) < 10:
                market_orders.append(["HIRE"])

    # Produce Selling
    shed_total = sum(state.shed.values())
    for item, count in state.shed.items():
        if not count or count <= 0 or item in ("seed", "fertilizer_seed"):
            continue

        if item == "WHEAT" and animals:
            sellable = max(0, count - len(animals) * 3)
        else:
            sellable = count

        if sellable <= 0:
            continue

        cur_price = state.price(item)
        score = market.sell_score(item)
        batch_size = min(10, sellable)

        should_sell = False
        if state.day >= 26:
            should_sell = True
        elif shed_total >= 50:
            should_sell = True
        elif item in ("MILK", "WOOL", "EGG", "FERTILIZER"):
            should_sell = True
        elif item == "MELON":
            if cur_price >= 160 or score >= 200 or sellable >= 15:
                should_sell = True
        elif cur_price >= 80:
            should_sell = True

        if should_sell and len(market_orders) < 10:
            market_orders.append(["SELL", item, batch_size])

    # Seed Purchases
    empty_tiles = board.empty_tiles_count
    target = min(12, empty_tiles)
    if crop and eco.should_buy_seed(crop, target) and len(market_orders) < 10:
        qty = target - state.seed_count(crop)
        if qty > 0:
            market_orders.append(["BUY_SEED", crop, qty])

    return market_orders[:10]
