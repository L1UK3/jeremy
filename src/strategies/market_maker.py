"""Dynamic market pricing, demand simulation, and order prioritization for Jeremy V3."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any

from environment.board import CROP_SPECS
from parameters import (
    DEFAULT_PARAMETERS,
    MarketMakerParams,
    get_active_parameters,
)

if TYPE_CHECKING:
    from environment.board import Board
    from environment.state import GameState

__all__ = [
    "BASE_PRICE",
    "CENTER_ITEMS",
    "GLUT_WEIGHT",
    "I0",
    "MP",
    "PRICE_FLOOR",
    "SELLABLE",
    "SHOP_DEMAND",
    "SUPPLY_DRIVER",
    "apply_market_controller",
    "cash_needed",
    "compute_analytical_supply",
    "count_driver",
    "mprice",
    "mshape",
    "opponent_scale",
    "plan_sells",
    "race_factor",
    "remaining_drain",
    "reserve_price",
    "sell_priority",
]

SELLABLE: tuple[str, ...] = (
    "STRAWBERRY",
    "MELON",
    "MILK",
    "WOOL",
    "EGG",
    "TOMATO",
    "CARROT",
    "WHEAT",
    "FERTILIZER",
)

FRONT_RUN_HORIZON: int = DEFAULT_PARAMETERS.market_maker.front_run_horizon
FRONT_RUN_ITEMS: tuple[str, ...] = ("MELON", "STRAWBERRY", "MILK", "WOOL")
BASE_PRICE: dict[str, int] = {
    "MELON": 250,
    "STRAWBERRY": 120,
    "MILK": 160,
    "WOOL": 200,
}
GLUT_WEIGHT: dict[str, float] = {
    "MELON": DEFAULT_PARAMETERS.market_maker.glut_weight_melon,
    "STRAWBERRY": DEFAULT_PARAMETERS.market_maker.glut_weight_strawberry,
    "MILK": DEFAULT_PARAMETERS.market_maker.glut_weight_milk,
    "WOOL": DEFAULT_PARAMETERS.market_maker.glut_weight_wool,
}

I0: int = 10000
PRICE_FLOOR: int = 1
MP: dict[str, tuple[int, int, str, float, str, float]] = {
    "WHEAT": (25, 400, "sqrt", 0.80, "log", 0.20),
    "CARROT": (35, 450, "log", 0.20, "sqrt", 0.70),
    "TOMATO": (60, 200, "linear", 0.40, "sqrt", 0.60),
    "STRAWBERRY": (120, 100, "sqrt", 0.70, "linear", 1.60),
    "MELON": (250, 300, "log", 0.20, "sq", 3.60),
    "EGG": (50, 332, "linear", 0.40, "log", 0.20),
    "MILK": (160, 122, "sqrt", 0.60, "linear", 1.60),
    "WOOL": (200, 105, "log", 0.20, "sq", 3.20),
    "FERTILIZER": (100, 200, "linear", 0.40, "linear", 0.40),
}
SHOP_DEMAND: dict[str, tuple[str, ...]] = {
    "BAKERY": ("EGG", "WHEAT"),
    "PIZZA_SHOP": ("MILK", "TOMATO", "WHEAT"),
    "BRUNCH_SPOT": ("EGG", "WHEAT", "STRAWBERRY"),
    "YARN_STORE": ("WOOL",),
    "ICE_CREAM_SHOP": ("STRAWBERRY", "MILK", "WHEAT"),
    "PET_CAFE": ("CARROT",),
    "SMOOTHIE_SHOP": ("STRAWBERRY", "MILK"),
    "FARMERS_MARKET": ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY"),
}
CENTER_ITEMS: tuple[str, ...] = tuple(k for k in MP if k != "FERTILIZER")

RESERVE: dict[str, float] = {}
SORT_SELLS: bool = DEFAULT_PARAMETERS.market_maker.sort_sells
SORT_KEY: str = DEFAULT_PARAMETERS.market_maker.sort_key
SELLS_FIRST: bool = DEFAULT_PARAMETERS.market_maker.sells_first
PROMOTE: tuple[str, ...] = ("MELON", "STRAWBERRY", "MILK", "WOOL")
RACE_WEIGHT: float = DEFAULT_PARAMETERS.market_maker.race_weight
PROMOTE_AFTER: dict[str, int] = {}
PROMOTE_IF_OPP_MONEY: dict[str, float] = {}
LIFT: tuple[str, ...] = ()
EARLY_TERMINAL: int = DEFAULT_PARAMETERS.market_maker.early_terminal
SHED_PRESSURE: int = DEFAULT_PARAMETERS.market_maker.shed_pressure
RAMP_START: int = DEFAULT_PARAMETERS.market_maker.ramp_start
RAMP_END: int = DEFAULT_PARAMETERS.market_maker.ramp_end

SUPPLY_DRIVER: dict[str, tuple[str, str | None]] = {
    "MILK": ("animal", "COW"),
    "WOOL": ("animal", "SHEEP"),
    "EGG": ("animal", "GOOSE"),
    "FERTILIZER": ("animal", None),
    "STRAWBERRY": ("crop", "STRAWBERRY"),
    "MELON": ("crop", "MELON"),
    "WHEAT": ("crop", "WHEAT"),
    "CARROT": ("crop", "CARROT"),
    "TOMATO": ("crop", "TOMATO"),
}


def compute_analytical_supply(
    item: str,
    step: int,
    state: GameState,
    board: Board,
) -> float:
    """Project remaining commodity supply over the season using active assets and game specs."""
    driver = SUPPLY_DRIVER.get(item)
    if driver is None:
        return float(PRICE_FLOOR)

    remaining_steps = max(0, 720 - step)
    remaining_days = remaining_steps / 24.0

    shed_stock = float(state.inventory(item))

    standing_yield = 0.0
    kind, name = driver

    unlocked_quads = float(
        len(state.unlocked_quadrants) if state.unlocked_quadrants else 1
    )
    quadrant_multiplier = 0.5 + 0.5 * (unlocked_quads / 4.0)

    if kind == "animal":
        animals = (
            [t for t in board.animals() if t.animal == name]
            if name
            else board.animals()
        )
        for t in animals:
            standing_yield += float(t.yield_units)

        active_count = float(len(animals)) + float(state.inventory(name or ""))
        future_yield = (
            active_count * remaining_days * 1.5 if active_count > 0 else 0.0
        )
    else:
        crops = board.crops(name) if name else []
        for t in crops:
            standing_yield += float(t.yield_units)

        active_count = float(len(crops))
        spec = CROP_SPECS.get(name or "")
        cycle_days = (
            float(spec.max_yield_day)
            if spec and spec.max_yield_day > 0
            else 4.0
        )
        yield_per_cycle = (
            float(spec.max_yield) if spec and spec.max_yield > 0 else 4.0
        )
        is_ongoing = spec.ongoing if spec else False

        seed_stock = float(state.seeds.get(name or "", 0))
        empty_unlocked = float(board.empty_tiles_count)

        if active_count > 0:
            effective_tiles = (
                active_count + min(seed_stock, empty_unlocked * 0.25)
            ) * quadrant_multiplier
            if is_ongoing:
                future_yield = effective_tiles * remaining_days * 1.0
            else:
                cycles = remaining_days / cycle_days
                future_yield = effective_tiles * cycles * yield_per_cycle
        elif seed_stock > 0 and empty_unlocked > 0:
            effective_tiles = (
                min(seed_stock, empty_unlocked * 0.5) * quadrant_multiplier
            )
            if is_ongoing:
                future_yield = effective_tiles * remaining_days * 1.0
            else:
                cycles = remaining_days / cycle_days
                future_yield = effective_tiles * cycles * yield_per_cycle
        else:
            future_yield = 0.0

    return max(float(PRICE_FLOOR), shed_stock + standing_yield + future_yield)


def mshape(func: str, x: float) -> float:
    """Non-linear pricing curve shape mapping."""
    if func == "linear":
        return x
    if func == "sq":
        return x * x
    if func == "sqrt":
        return math.sqrt(x)
    if func == "log10":
        return math.log10(1.0 + x)
    return math.log(1.0 + x)


def mprice(item: str, inventory: float | int) -> int:
    """Exact port of engine's market_price."""
    base, throughput, below_f, below_t, above_f, above_t = MP[item]
    if inventory < I0:
        amp = below_t * base / mshape(below_f, throughput)
        value = base + amp * mshape(below_f, I0 - inventory)
    else:
        amp = above_t * base / mshape(above_f, throughput)
        value = base - amp * mshape(above_f, inventory - I0)
    return max(PRICE_FLOOR, round(value))


def remaining_drain(item: str, step: int, shops: list[str]) -> float:
    """Calculate town demand consumption from step to season end."""
    if item == "FERTILIZER":
        return 0.0
    unlocked = set(shops or ())
    live = 0
    pending: list[int] = []
    for name, products in SHOP_DEMAND.items():
        if item not in products:
            continue
        weight = 2 if len(products) == 1 else 1
        if name in unlocked:
            live += weight
        else:
            pending.append(weight)
    n_locked = len(SHOP_DEMAND) - len(unlocked)
    pending_total = sum(pending)
    is_center = item in CENTER_ITEMS
    total = 0.0
    for s in range(step, 720):
        day = s // 24
        if s % 4 == 0:
            total += live
            if pending_total and n_locked > 0:
                expected = min(n_locked, max(0, day // 3 + 1 - len(unlocked)))
                total += pending_total * (expected / n_locked)
        if is_center and s % 12 == 0:
            total += 4 if day >= 20 else (2 if day >= 10 else 1)
    return total


def count_driver(farm: dict[str, Any], kind: str, name: str | None) -> int:
    """Count asset producers on farm."""
    total = 0
    for row in farm.get("tiles", []) or []:
        for tile in row or []:
            if not isinstance(tile, dict):
                continue
            if kind == "animal":
                animal = tile.get("animal")
                if animal and (name is None or animal == name):
                    total += 1
            elif tile.get("kind") == "PLANT" and tile.get("crop") == name:
                total += 1
    return total


def opponent_scale(state: GameState, board: Board, item: str) -> float:
    """Opponent's expected remaining supply relative to player."""
    driver = SUPPLY_DRIVER.get(item)
    if driver is None:
        return 1.0
    farms = state.raw.get("farms") or []
    if len(farms) < 2:
        return 1.0
    me = state.player
    kind, name = driver
    if kind == "animal":
        mine = (
            sum(1 for t in board.animals() if t.animal == name)
            if name
            else len(board.animals())
        )
    else:
        mine = len(board.crops(name)) if name else 0
    theirs = count_driver(farms[1 - me], kind, name)
    if mine <= 0:
        return 1.0 if theirs > 0 else 0.0
    return max(0.0, min(2.0, theirs / float(mine)))


def reserve_price(
    item: str,
    step: int,
    state: GameState,
    board: Board,
    shops: list[str],
    scale: float = 1.0,
    params: MarketMakerParams | None = None,
) -> float:
    """Reservation price calculation for inventory hold/sell decisions."""
    mp = params or get_active_parameters().market_maker
    if item not in MP:
        return float(PRICE_FLOOR)
    base = MP[item][0]
    frac = scale
    if step >= mp.ramp_start:
        span = float(max(1, mp.ramp_end - mp.ramp_start))
        frac *= max(0.0, (mp.ramp_end - step) / span)
    drain = remaining_drain(item, step, shops)
    supply = compute_analytical_supply(item, step, state, board)
    ahead = supply * (1.0 + opponent_scale(state, board, item))
    if ahead > 0.0:
        frac *= min(1.0, drain / ahead)
    return max(float(PRICE_FLOOR), base * frac)


def plan_sells(
    state: GameState,
    board: Board,
    step: int,
    slots: int,
    short_of_cash: float,
    reservation_scales: dict[str, float] | None = None,
    params: MarketMakerParams | None = None,
) -> list[list[Any]]:
    """Select optimal SELL orders for controlled products."""
    mp = params or get_active_parameters().market_maker
    reserve = reservation_scales if reservation_scales is not None else RESERVE
    if slots <= 0 or not reserve:
        return []
    shed = state.shed
    inventory = (state.raw.get("market") or {}).get("inventory") or {}
    shops = (state.raw.get("town") or {}).get("unlocked_shops") or []
    load = sum(max(0, int(v or 0)) for v in shed.values())
    forced = load >= mp.shed_pressure or short_of_cash > 0

    candidates: list[tuple[int, str, int]] = []
    for item, scale in reserve.items():
        held = state.inventory(item)
        if held <= 0:
            continue
        inv = int(inventory.get(item, I0) or I0)
        if forced:
            units = held
        else:
            res_val = reserve_price(
                item, step, state, board, shops, scale=scale, params=mp
            )
            units = 0
            while units < held and mprice(item, inv + units) >= res_val:
                units += 1
        if units > 0:
            candidates.append((mprice(item, inv) * units, item, units))
    candidates.sort(reverse=True)
    return [["SELL", item, units] for _, item, units in candidates[:slots]]


def cash_needed(orders: list[Any], state: GameState) -> int:
    """Estimate gold requirement for this turn's buy orders."""
    seeds = {
        "WHEAT": 10,
        "CARROT": 20,
        "TOMATO": 50,
        "STRAWBERRY": 100,
        "MELON": 80,
    }
    animals = {"GOOSE": 300, "COW": 400, "SHEEP": 500}
    prices = state.prices
    total = 0
    for order in orders:
        if not isinstance(order, list) or not order:
            continue
        op = order[0]
        if op == "BUY_SEED" and len(order) >= 3:
            total += seeds.get(order[1], 0) * int(order[2] or 0)
        elif op == "BUY_ANIMAL" and len(order) >= 3:
            total += animals.get(order[1], 0) * int(order[2] or 0)
        elif op == "BUY_PRODUCT" and len(order) >= 3:
            total += int(prices.get(order[1], 50) or 50) * int(order[2] or 0)
        elif op == "BUY_LAND":
            total += 4000
    return total


def race_factor(
    item: str,
    step: int,
    state: GameState,
    board: Board,
    params: MarketMakerParams | None = None,
) -> float:
    """Glut factor adjusting slot priority for oversupplied items."""
    mp = params or get_active_parameters().market_maker
    if mp.race_weight <= 0.0:
        return 1.0
    shops = (state.raw.get("town") or {}).get("unlocked_shops") or []
    drain = remaining_drain(item, step, shops)
    supply = compute_analytical_supply(item, step, state, board)
    ahead = supply * (1.0 + opponent_scale(state, board, item))
    if ahead <= 0.0:
        return 1.0
    glut = max(0.0, 1.0 - drain / ahead)
    return 1.0 + mp.race_weight * glut


def sell_priority(
    order: Any,
    state: GameState,
    board: Board,
    step: int = 0,
    params: MarketMakerParams | None = None,
) -> float:
    """Priority ranking for ordering SELL orders in market resolution queue."""
    if not (isinstance(order, list) and len(order) >= 3 and order[0] == "SELL"):
        return -1.0
    item = order[1]
    try:
        qty = int(order[2] or 0)
    except (TypeError, ValueError):
        return -1.0
    if qty <= 0 or item not in MP:
        return -1.0
    mp = params or get_active_parameters().market_maker
    inventory = (state.raw.get("market") or {}).get("inventory") or {}
    inv = int(inventory.get(item, I0) or I0)
    unit = mprice(item, inv)
    held = state.inventory(item)
    qty = min(qty, held) if held > 0 else qty
    race = race_factor(item, step, state, board, params=mp)
    if mp.sort_key == "unit":
        return float(unit) * race
    if mp.sort_key == "impact":
        return float(qty) * float(unit - mprice(item, inv + qty)) * race
    return float(unit) * float(qty) * race


def apply_market_controller(
    action: dict[str, Any],
    state: GameState,
    board: Board,
    step: int,
    reservation_scales: dict[str, float] | None = None,
    params: MarketMakerParams | None = None,
) -> dict[str, Any]:
    """Apply market ordering, slot promotion, and early liquidation."""
    mp = params or get_active_parameters().market_maker
    try:
        if mp.early_terminal and step == mp.early_terminal:
            rows: list[tuple[float, str, int]] = []
            for item in MP:
                held = state.inventory(item)
                if held > 0:
                    rows.append(
                        (
                            sell_priority(
                                ["SELL", item, held],
                                state,
                                board,
                                step,
                                params=mp,
                            ),
                            item,
                            held,
                        )
                    )
            if rows:
                rows.sort(reverse=True)
                action["market"] = [["SELL", i, q] for _p, i, q in rows[:10]]
                return action
        if step >= 717:
            return action

        orders = list(action.get("market") or [])
        reserve = (
            reservation_scales if reservation_scales is not None else RESERVE
        )
        keep = [
            order
            for order in orders
            if not (
                isinstance(order, list)
                and len(order) >= 2
                and order[0] == "SELL"
                and order[1] in reserve
            )
        ]
        player = state.player
        money = float(state.money)
        short = max(0.0, cash_needed(keep, state) - money)
        sells = plan_sells(
            state,
            board,
            step,
            10 - len(keep),
            short,
            reservation_scales=reservation_scales,
            params=mp,
        )
        if not mp.sort_sells:
            action["market"] = (sells + keep)[:10]
            return action

        def is_sell(o: Any) -> bool:
            return isinstance(o, list) and bool(o) and o[0] == "SELL"

        opp_money: float | None = None
        if PROMOTE_IF_OPP_MONEY:
            farms = state.raw.get("farms") or []
            if len(farms) > 1:
                opp_money = float(farms[1 - player].get("money", 0) or 0)

        def promotable(o: Any) -> bool:
            if not is_sell(o):
                return False
            item = o[1]
            if item in PROMOTE_IF_OPP_MONEY:
                if opp_money is None:
                    return False
                return opp_money >= PROMOTE_IF_OPP_MONEY[item]
            if item in PROMOTE_AFTER:
                return step >= PROMOTE_AFTER[item]
            return not PROMOTE or item in PROMOTE

        if LIFT:
            lifted = [o for o in keep if is_sell(o) and o[1] in LIFT]
            if lifted:
                lifted.sort(
                    key=lambda o: (
                        -sell_priority(o, state, board, step, params=mp)
                    )
                )
                held = [o for o in keep if not (is_sell(o) and o[1] in LIFT)]
                keep = lifted + held

        merged = [o for o in sells if promotable(o)] + [
            o for o in keep if promotable(o)
        ]
        merged.sort(
            key=lambda o: -sell_priority(o, state, board, step, params=mp)
        )
        rest = [o for o in sells if not promotable(o)] + [
            o for o in keep if not promotable(o)
        ]
        if mp.sells_first:
            action["market"] = (merged + rest)[:10]
        else:
            out: list[list[Any]] = []
            queue = list(merged)
            for order in keep:
                out.append(
                    queue.pop(0) if (promotable(order) and queue) else order
                )
            out.extend(queue)
            action["market"] = out[:10]
        return action
    except Exception:
        return action
