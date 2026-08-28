from __future__ import annotations

from typing import TYPE_CHECKING

from src.v0.environment.board import step_toward

if TYPE_CHECKING:
    from src.v0.agent.planner import Planner


def manage_livestock(
    planner: Planner,
    worker_idx: int = 0,
    worker_pos: tuple[int, int] | None = None,
) -> list[str] | None:
    """Execute complete livestock care chore routine (pickup wheat -> feed -> care -> collect -> drop)."""
    animals = planner.board.animals()
    if not animals:
        return None

    fx, fy = worker_pos if worker_pos is not None else planner.state.farmer
    inv = planner.state.worker_inventory(worker_idx)
    carried_wheat = inv.get("WHEAT", 0)
    has_byproducts = any(
        inv.get(p, 0) > 0 for p in ("FERTILIZER", "MILK", "WOOL", "EGG")
    )

    needs_feed = planner.board.needs_feed()
    needs_care = planner.board.needs_care()
    needs_fert = planner.board.has_fertilizer_tiles()
    needs_prod_harvest = [t for t in animals if t.yield_units > 0]

    # If standing on an animal tile, perform available actions on that tile first
    current_tile = planner.board.tile(fx, fy)
    if current_tile and current_tile.is_animal:
        if not current_tile.fed_today and carried_wheat > 0:
            return ["FEED"]
        if not current_tile.cared_today:
            return ["CARE"]
        if current_tile.fertilizer_available:
            return ["COLLECT_FERTILIZER"]
        if current_tile.yield_units > 0:
            return ["HARVEST"]

    # If animals need feed and we have no wheat in hand
    if needs_feed and carried_wheat == 0:
        shed_wheat = planner.state.inventory("WHEAT")
        if shed_wheat > 0:
            if planner.state.is_shed_adjacent(fx, fy):
                pickup_qty = min(len(needs_feed), shed_wheat)
                return ["PICKUP", "WHEAT", str(pickup_qty)]
            else:
                target_shed = planner.board.nearest_shed(fx, fy)
                step = step_toward(fx, fy, target_shed[0], target_shed[1])
                return [step] if step != "PASS" else ["PASS"]

    # If we are carrying wheat and animals need feed, go feed nearest unfed animal
    if needs_feed and carried_wheat > 0:
        target = planner.board.nearest_to(fx, fy, needs_feed)
        if target:
            step = step_toward(fx, fy, target.x, target.y)
            return [step] if step != "PASS" else ["PASS"]

    # If animals need care, go care for nearest
    if needs_care:
        target = planner.board.nearest_to(fx, fy, needs_care)
        if target:
            step = step_toward(fx, fy, target.x, target.y)
            return [step] if step != "PASS" else ["PASS"]

    # If animals have fertilizer, go collect
    if needs_fert:
        target = planner.board.nearest_to(fx, fy, needs_fert)
        if target:
            step = step_toward(fx, fy, target.x, target.y)
            return [step] if step != "PASS" else ["PASS"]

    # If animals have milk/wool ready, go harvest
    if needs_prod_harvest:
        target = planner.board.nearest_to(fx, fy, needs_prod_harvest)
        if target:
            step = step_toward(fx, fy, target.x, target.y)
            return [step] if step != "PASS" else ["PASS"]

    # If all animal chores are done, but worker is carrying byproducts, deposit at shed
    if has_byproducts:
        if planner.state.is_shed_adjacent(fx, fy):
            return ["DROP"]
        else:
            target_shed = planner.board.nearest_shed(fx, fy)
            step = step_toward(fx, fy, target_shed[0], target_shed[1])
            return [step] if step != "PASS" else ["PASS"]

    return None
