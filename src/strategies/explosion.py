from __future__ import annotations

from typing import TYPE_CHECKING, Any, NamedTuple

from environment.board import CROP_SPECS, step_toward
from parameters import (
    DEFAULT_PARAMETERS,
    ExplosionParams,
    get_active_parameters,
)

if TYPE_CHECKING:
    from environment.board import Board
    from environment.state import GameState

__all__ = [
    "SELLABLE",
    "explosion",
    "is_valid_terminal_water",
    "pre_terminal_liquidation",
]

SELLABLE: tuple[str, ...] = (
    "MELON",
    "WOOL",
    "MILK",
    "STRAWBERRY",
    "EGG",
    "TOMATO",
    "CARROT",
    "WHEAT",
    "FERTILIZER",
)

GLUT_WEIGHT: dict[str, float] = {
    "MELON": DEFAULT_PARAMETERS.explosion.terminal_glut_weight_melon,
    "WOOL": DEFAULT_PARAMETERS.explosion.terminal_glut_weight_wool,
    "MILK": DEFAULT_PARAMETERS.explosion.terminal_glut_weight_milk,
    "STRAWBERRY": DEFAULT_PARAMETERS.explosion.terminal_glut_weight_strawberry,
    "EGG": DEFAULT_PARAMETERS.explosion.terminal_glut_weight_egg,
    "TOMATO": DEFAULT_PARAMETERS.explosion.terminal_glut_weight_tomato,
    "CARROT": 1.0,
    "WHEAT": 1.0,
    "FERTILIZER": 1.0,
}

ANIMAL_PRODUCT: dict[str, str] = {
    "COW": "MILK",
    "SHEEP": "WOOL",
    "GOOSE": "EGG",
}

SHED_ACCESS: tuple[tuple[int, int], ...] = ((4, 4), (5, 4), (4, 5), (5, 5))
SHED_CAPACITY: int = 100
MAX_MARKET_ORDERS: int = 10


class HarvestTarget(NamedTuple):
    pos: tuple[int, int]
    value: float
    dist_to_shed: int


def _shed_nav(x: int, y: int) -> tuple[int, tuple[int, int]]:
    """Return (min_distance_to_shed, nearest_shed_coord)."""
    nearest = min(
        SHED_ACCESS,
        key=lambda s: (abs(s[0] - x) + abs(s[1] - y), s[1], s[0]),
    )
    return abs(nearest[0] - x) + abs(nearest[1] - y), nearest


def is_valid_terminal_water(tile: Any, day: int) -> bool:
    """Evaluate whether a plant tile should be watered during termination.

    During termination (day >= 28), watering is restricted strictly to one-time
    crops within their bonus watering window that produce an immediate yield
    bonus on the turn of the action. Ongoing crops and crops that cannot mature
    before Step 720 are suppressed.
    """
    crop = getattr(tile, "crop", None)
    if not crop:
        return False
    spec = CROP_SPECS.get(crop)
    if spec is None:
        return False

    planted_day = getattr(tile, "planted_day", 0)

    # Ongoing crops never yield immediately on water; Day 29 midnight yield cannot be harvested
    if spec.ongoing:
        if day >= 28 or (planted_day + spec.first_yield_day >= 29):
            return False
        return True

    # One-time crops:
    if planted_day + spec.first_yield_day >= 30:
        return False

    crop_age = tile.age(day) if hasattr(tile, "age") else (day - planted_day)
    bonus_start = (spec.max_yield_day + 1) // 2

    # During late termination (day >= 28), only water if inside the immediate bonus window
    if day >= 28:
        return bonus_start <= crop_age <= spec.max_yield_day

    return True


def _collect_harvest_targets(
    state: GameState, board: Board
) -> list[HarvestTarget]:
    """Collect unharvested plants, animal yields, available fertilizer, and immediate-yield bonus crops."""
    targets: list[HarvestTarget] = []
    prices = state.prices

    for tile in board.all_tiles():
        if tile.is_plant and tile.crop:
            if tile.yield_units > 0:
                val = float(tile.yield_units * max(1, prices.get(tile.crop, 1)))
                dist, _ = _shed_nav(tile.x, tile.y)
                targets.append(HarvestTarget(tile.pos, val, dist))
            elif is_valid_terminal_water(tile, state.day) and not tile.watered:
                bonus = (
                    2
                    if getattr(tile, "fertilized_until_day", -1) >= state.day
                    else 1
                )
                val = float(bonus * max(1, prices.get(tile.crop, 1)))
                dist, _ = _shed_nav(tile.x, tile.y)
                targets.append(HarvestTarget(tile.pos, val, dist))
        elif tile.is_animal and tile.animal:
            if tile.yield_units > 0:
                prod = ANIMAL_PRODUCT.get(tile.animal, tile.animal)
                val = float(tile.yield_units * max(1, prices.get(prod, 1)))
                dist, _ = _shed_nav(tile.x, tile.y)
                targets.append(HarvestTarget(tile.pos, val, dist))
            elif tile.fertilizer_available:
                val = float(max(1, prices.get("FERTILIZER", 1)))
                dist, _ = _shed_nav(tile.x, tile.y)
                targets.append(HarvestTarget(tile.pos, val, dist))

    return targets


def _dispatch_worker(
    worker_idx: int,
    wx: int,
    wy: int,
    turns_left: int,
    state: GameState,
    board: Board,
    targets: list[HarvestTarget],
    claimed_tiles: set[tuple[int, int]],
    pending_deposits: dict[str, int],
    remaining_seeds: dict[str, int] | None = None,
) -> list[str]:
    """Determine reachability-bounded optimal action for one worker."""
    inv = state.worker_inventory(worker_idx)
    load = sum(max(0, count) for count in inv.values())
    dist_to_shed, nearest_shed = _shed_nav(wx, wy)

    if load > 0 and (wx, wy) in SHED_ACCESS:
        for item, count in inv.items():
            if count > 0 and item in SELLABLE:
                pending_deposits[item] = pending_deposits.get(item, 0) + count
        return ["DROP"]

    if load > 0 and (load >= 2 or dist_to_shed + 2 >= turns_left):
        return [step_toward(wx, wy, nearest_shed[0], nearest_shed[1])]

    tile = board.tile(wx, wy)
    if tile and (dist_to_shed + 2 <= turns_left):
        if tile.yield_units > 0:
            claimed_tiles.add((wx, wy))
            return ["HARVEST"]
        if tile.is_animal and tile.fertilizer_available:
            claimed_tiles.add((wx, wy))
            return ["COLLECT_FERTILIZER"]
        if (
            tile.is_plant
            and not tile.watered
            and is_valid_terminal_water(tile, state.day)
        ):
            claimed_tiles.add((wx, wy))
            return ["WATER"]

    best_target: HarvestTarget | None = None
    best_score: float = -1.0

    for target in targets:
        if target.pos in claimed_tiles:
            continue
        tx, ty = target.pos
        total_turns = abs(wx - tx) + abs(wy - ty) + target.dist_to_shed + 2
        if total_turns <= turns_left:
            score = target.value / float(total_turns)
            if score > best_score:
                best_score = score
                best_target = target

    if best_target is not None:
        claimed_tiles.add(best_target.pos)
        return [step_toward(wx, wy, best_target.pos[0], best_target.pos[1])]

    if load > 0:
        return [step_toward(wx, wy, nearest_shed[0], nearest_shed[1])]

    seeds_stock = (
        remaining_seeds
        if remaining_seeds is not None
        else {
            c: state.seed_count(c)
            for c in ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON")
        }
    )
    for crop in ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON"):
        if seeds_stock.get(crop, 0) > 0:
            current_tile = board.tile(wx, wy)
            if (
                current_tile is not None
                and state.is_tile_unlocked(wx, wy)
                and current_tile.empty
                and (wx, wy) not in claimed_tiles
            ):
                claimed_tiles.add((wx, wy))
                seeds_stock[crop] -= 1
                return ["PLANT", crop]

            empty_candidates = [
                t.pos
                for t in board.empty_tiles(only_unlocked=True)
                if t.pos not in claimed_tiles
            ]
            if empty_candidates:
                best_empty = min(
                    empty_candidates,
                    key=lambda p: abs(p[0] - wx) + abs(p[1] - wy),
                )
                claimed_tiles.add(best_empty)
                return [step_toward(wx, wy, best_empty[0], best_empty[1])]

    return ["PASS"]


def _build_market_orders(
    state: GameState,
    pending_deposits: dict[str, int],
    params: ExplosionParams | None = None,
) -> list[list[Any]]:
    """Build glut-weighted sell orders including same-turn projected deposits."""
    ep = params or get_active_parameters().explosion
    weights = {
        "MELON": ep.terminal_glut_weight_melon,
        "WOOL": ep.terminal_glut_weight_wool,
        "MILK": ep.terminal_glut_weight_milk,
        "STRAWBERRY": ep.terminal_glut_weight_strawberry,
        "EGG": ep.terminal_glut_weight_egg,
        "TOMATO": ep.terminal_glut_weight_tomato,
        "CARROT": 1.0,
        "WHEAT": 1.0,
        "FERTILIZER": 1.0,
    }
    projected = {k: max(0, int(state.shed.get(k, 0))) for k in SELLABLE}
    cap = sum(projected.values())

    for item, count in pending_deposits.items():
        take = min(count, max(0, SHED_CAPACITY - cap))
        if take > 0:
            projected[item] += take
            cap += take

    sells = [
        (
            float(state.price(item) * qty) * weights.get(item, 1.0),
            item,
            qty,
        )
        for item in SELLABLE
        if (qty := projected.get(item, 0)) > 0
    ]
    sells.sort(key=lambda entry: entry[0], reverse=True)
    return [
        ["SELL", item, min(100, qty)]
        for _, item, qty in sells[:MAX_MARKET_ORDERS]
    ]


def pre_terminal_liquidation(
    action: dict[str, Any],
    state: GameState,
    step: int,
    params: ExplosionParams | None = None,
) -> dict[str, Any]:
    ep = params or get_active_parameters().explosion
    if step < ep.pre_terminal_step:
        return action
    market = action.setdefault("market", [])
    already = {
        order[1]
        for order in market
        if isinstance(order, list) and len(order) >= 2 and order[0] == "SELL"
    }
    for item in SELLABLE:
        qty = state.inventory(item)
        if qty > 0 and item not in already and len(market) < MAX_MARKET_ORDERS:
            market.append(["SELL", item, qty])
    return action


def explosion(
    state: GameState,
    board: Board,
    params: ExplosionParams | None = None,
) -> dict[str, Any]:
    """Final 8-turn liquidation controller (turns 712-719)."""
    ep = params or get_active_parameters().explosion
    turns_left = max(1, 720 - state.step)
    targets = _collect_harvest_targets(state, board)
    claimed_tiles: set[tuple[int, int]] = set()
    pending_deposits: dict[str, int] = {}

    positions = [
        state.farmer,
        *(tuple(h) for h in state.hands),
    ]
    remaining_seeds = {
        c: state.seed_count(c)
        for c in ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON")
    }
    acts = [
        _dispatch_worker(
            idx,
            pos[0],
            pos[1],
            turns_left,
            state,
            board,
            targets,
            claimed_tiles,
            pending_deposits,
            remaining_seeds=remaining_seeds,
        )
        for idx, pos in enumerate(positions)
    ]

    market_orders = _build_market_orders(state, pending_deposits, params=ep)
    return {"farmer": acts[0], "hands": acts[1:], "market": market_orders}
