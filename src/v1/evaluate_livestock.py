from board import Board, step_toward
from state import GameState

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
