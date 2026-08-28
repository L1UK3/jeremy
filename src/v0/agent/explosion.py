from __future__ import annotations

from typing import TYPE_CHECKING, Any, NamedTuple

from src.v0.environment.actions import Action
from src.v0.environment.board import step_toward

if TYPE_CHECKING:
    from src.v0.agent.planner import Planner
    from src.v0.environment.state import GameState

__all__ = ["explosion"]

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
    "MELON": 3.6,
    "WOOL": 3.2,
    "MILK": 2.0,
    "STRAWBERRY": 2.0,
    "EGG": 1.5,
    "TOMATO": 1.3,
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


def _collect_harvest_targets(planner: Planner) -> list[HarvestTarget]:
    """Collect unharvested plants, animal yields, and available fertilizer."""
    targets: list[HarvestTarget] = []
    prices = planner.state.prices

    for tile in planner.board.all_tiles():
        if tile.is_plant and tile.yield_units > 0 and tile.crop:
            val = float(tile.yield_units * max(1, prices.get(tile.crop, 1)))
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
    planner: Planner,
    targets: list[HarvestTarget],
    claimed_tiles: set[tuple[int, int]],
    pending_deposits: dict[str, int],
) -> list[str]:
    """Determine reachability-bounded optimal action for one worker."""
    inv = planner.state.worker_inventory(worker_idx)
    load = sum(max(0, count) for count in inv.values())
    dist_to_shed, nearest_shed = _shed_nav(wx, wy)

    if load > 0 and (wx, wy) in SHED_ACCESS:
        for item, count in inv.items():
            if count > 0 and item in SELLABLE:
                pending_deposits[item] = pending_deposits.get(item, 0) + count
        return ["DROP"]

    if load > 0 and (dist_to_shed + 1 >= turns_left):
        return [step_toward(wx, wy, nearest_shed[0], nearest_shed[1])]

    tile = planner.board.get_tile(wx, wy)
    if tile and (dist_to_shed + 2 <= turns_left):
        if tile.yield_units > 0:
            claimed_tiles.add((wx, wy))
            return ["HARVEST"]
        if tile.is_animal and tile.fertilizer_available:
            claimed_tiles.add((wx, wy))
            return ["COLLECT_FERTILIZER"]

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

    return ["PASS"]


def _build_market_orders(
    state: GameState, pending_deposits: dict[str, int]
) -> list[list[Any]]:
    """Build glut-weighted sell orders including same-turn projected deposits."""
    projected = {k: max(0, int(state.shed.get(k, 0))) for k in SELLABLE}
    cap = sum(projected.values())

    for item, count in pending_deposits.items():
        take = min(count, max(0, SHED_CAPACITY - cap))
        if take > 0:
            projected[item] += take
            cap += take

    sells = [
        (float(state.price(item) * qty) * GLUT_WEIGHT.get(item, 1.0), item, qty)
        for item in SELLABLE
        if (qty := projected.get(item, 0)) > 0
    ]
    sells.sort(key=lambda entry: entry[0], reverse=True)
    return [
        ["SELL", item, min(100, qty)]
        for _, item, qty in sells[:MAX_MARKET_ORDERS]
    ]


def explosion(planner: Planner) -> Action:
    """Final 8-turn liquidation controller (turns 712-719)."""
    turns_left = max(1, 720 - planner.state.step)
    targets = _collect_harvest_targets(planner)
    claimed_tiles: set[tuple[int, int]] = set()
    pending_deposits: dict[str, int] = {}

    positions = [
        planner.state.farmer,
        *(tuple(h) for h in planner.state.hands),
    ]
    acts = [
        _dispatch_worker(
            idx,
            pos[0],
            pos[1],
            turns_left,
            planner,
            targets,
            claimed_tiles,
            pending_deposits,
        )
        for idx, pos in enumerate(positions)
    ]

    market_orders = _build_market_orders(planner.state, pending_deposits)
    return Action(farmer=acts[0], hands=acts[1:], market=market_orders)
