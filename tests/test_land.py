"""Episode invariant tests for Land Expansion economics, timing, and state transitions."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from src.strategies.procurement import FIBONACCI

if TYPE_CHECKING:
    from tests.conftest import EpisodeTrace

LAND_COSTS = {"NE": 1000, "SW": 2000, "SE": 4000}
CROP_SEED_PRICES = {
    "WHEAT": 10,
    "CARROT": 15,
    "TOMATO": 30,
    "STRAWBERRY": 60,
    "MELON": 120,
}


def _identify_active_crop(tiles: list[list]) -> str:
    """Identify dominant active crop on the farm, defaulting to WHEAT."""
    crop_counts: dict[str, int] = {}
    for r in range(10):
        for c in range(10):
            t = tiles[r][c]
            if isinstance(t, dict) and t.get("kind") == "PLANT":
                crop = t.get("crop")
                if crop:
                    crop_counts[crop] = crop_counts.get(crop, 0) + 1
    if crop_counts:
        return max(crop_counts, key=crop_counts.get)
    return "WHEAT"


def test_land_purchase_economic_justification(episode_trace: EpisodeTrace) -> None:
    """BUY_LAND must only be emitted when treasury covers land + 25 tile seeds + maintenance crew."""
    seat = episode_trace.seat
    steps = episode_trace.steps

    for step_idx in range(1, len(steps)):
        act = steps[step_idx][seat].get("action") or {}
        market_acts = act.get("market", [])
        land_orders = [m for m in market_acts if m and m[0] == "BUY_LAND"]
        if not land_orders:
            continue

        obs_before = steps[step_idx - 1][seat].get("observation") or {}
        farm_before = obs_before.get("farms", [{}])[seat]
        money = farm_before.get("money", 0)
        unlocked = set(farm_before.get("unlocked_quadrants", []))

        # Determine next quadrant in order
        if "NE" not in unlocked:
            next_quad = "NE"
        elif "SW" not in unlocked:
            next_quad = "SW"
        elif "SE" not in unlocked:
            next_quad = "SE"
        else:
            pytest.fail(f"Step {step_idx}: Emitted BUY_LAND with all quadrants unlocked: {unlocked}")

        land_cost = LAND_COSTS[next_quad]
        active_crop = _identify_active_crop(farm_before.get("tiles", []))
        seed_cost = CROP_SEED_PRICES.get(active_crop, 10)
        tile_stocking_cost = 25 * seed_cost

        # Estimate crew maintenance for 25 additional tiles (at least 2 farm hands)
        crew_maintenance_cost = FIBONACCI[0] + FIBONACCI[1]  # $1 + $1 = $2 minimum
        total_required = land_cost + tile_stocking_cost + crew_maintenance_cost

        assert money >= total_required, (
            f"Step {step_idx}: BUY_LAND for {next_quad} lacked economic justification. "
            f"Treasury=${money}, required=${total_required} "
            f"(Land=${land_cost}, 25x {active_crop} Seeds=${tile_stocking_cost}, Crew=${crew_maintenance_cost})"
        )


def test_land_quadrant_unlock_transition(episode_trace: EpisodeTrace) -> None:
    """Following BUY_LAND, the target quadrant must unlock in step and deduct funds."""
    seat = episode_trace.seat
    steps = episode_trace.steps

    for step_idx in range(1, len(steps)):
        act = steps[step_idx][seat].get("action") or {}
        market_acts = act.get("market", [])
        if not any(m and m[0] == "BUY_LAND" for m in market_acts):
            continue

        obs_before = steps[step_idx - 1][seat].get("observation") or {}
        farm_before = obs_before.get("farms", [{}])[seat]
        unlocked_before = set(farm_before.get("unlocked_quadrants", []))

        if "NE" not in unlocked_before:
            expected_quad = "NE"
        elif "SW" not in unlocked_before:
            expected_quad = "SW"
        elif "SE" not in unlocked_before:
            expected_quad = "SE"
        else:
            continue

        cost = LAND_COSTS[expected_quad]

        obs_after = steps[step_idx][seat].get("observation") or {}
        farm_after = obs_after.get("farms", [{}])[seat]
        unlocked_after = set(farm_after.get("unlocked_quadrants", []))

        assert expected_quad in unlocked_after, (
            f"Step {step_idx}: Quadrant {expected_quad} failed to unlock after BUY_LAND."
        )
        assert farm_after.get("money", 0) <= farm_before.get("money", 0) - cost + 100, (
            f"Step {step_idx}: Money was not deducted properly for {expected_quad} purchase."
        )


def test_land_order_volume_limits(episode_trace: EpisodeTrace) -> None:
    """Agent must emit at most one BUY_LAND order per turn and at most 3 over the episode."""
    seat = episode_trace.seat
    steps = episode_trace.steps
    total_buys = 0

    for step_idx, step_data in enumerate(steps):
        act = step_data[seat].get("action") or {}
        land_orders = [m for m in act.get("market", []) if m and m[0] == "BUY_LAND"]
        assert len(land_orders) <= 1, (
            f"Step {step_idx}: Multiple BUY_LAND orders in single turn: {land_orders}"
        )
        total_buys += len(land_orders)

    assert total_buys <= 3, f"Episode exceeded maximum 3 quadrant purchases: total {total_buys}"
