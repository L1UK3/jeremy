"""Episode invariant tests for pasture/coop construction, animal procurement, and livestock care."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tests.conftest import EpisodeTrace


def test_structures_placed_on_empty_unlocked_tiles(episode_trace: EpisodeTrace) -> None:
    """Coop and Pasture construction must only be attempted on empty, unlocked tiles."""
    seat = episode_trace.seat
    steps = episode_trace.steps

    for step_idx, step_data in enumerate(steps):
        agent_step = step_data[seat]
        obs = agent_step.get("observation") or {}
        act = agent_step.get("action") or {}
        if not obs or "farms" not in obs:
            continue

        farm = obs["farms"][seat]
        tiles = farm.get("tiles", [])
        farmer_pos = farm.get("farmer")
        hands_pos = farm.get("hands", [])

        positions = [farmer_pos, *hands_pos]
        actions = [act.get("farmer", []), *act.get("hands", [])]

        for idx, (pos, a) in enumerate(zip(positions, actions, strict=False)):
            if not pos or not a:
                continue
            op = a[0]
            if op in ("BUILD_PASTURE", "BUILD_COOP"):
                x, y = pos
                current_tile = tiles[y][x]
                assert current_tile is None, (
                    f"Step {step_idx} Unit {idx} at ({x},{y}) executed {op} on non-empty tile: {current_tile}"
                )


def test_placed_animals_sustained_without_starvation(
    episode_trace: EpisodeTrace,
) -> None:
    """Placed livestock must be fed; consecutive_unfed must never reach 2 (causing animal escape)."""
    seat = episode_trace.seat
    steps = episode_trace.steps

    for step_idx, step_data in enumerate(steps):
        agent_step = step_data[seat]
        obs = agent_step.get("observation") or {}
        if not obs or "farms" not in obs:
            continue

        tiles = obs["farms"][seat].get("tiles", [])
        for r in range(10):
            for c in range(10):
                tile = tiles[r][c]
                if isinstance(tile, dict) and tile.get("kind") in ("COOP", "PASTURE"):
                    if "animal" in tile:
                        unfed = tile.get("consecutive_unfed", 0)
                        assert unfed < 2, (
                            f"Step {step_idx} at ({r},{c}): Animal {tile.get('animal')} "
                            f"reached {unfed} consecutive unfed days (critical starvation risk)."
                        )


def test_animal_purchases_within_housing_capacity(episode_trace: EpisodeTrace) -> None:
    """Animal purchases must respect farm capacity and shed limits."""
    seat = episode_trace.seat
    steps = episode_trace.steps

    for step_idx in range(1, len(steps)):
        act = steps[step_idx][seat].get("action") or {}
        obs_before = steps[step_idx - 1][seat].get("observation") or {}
        if not obs_before or "farms" not in obs_before or "private" not in obs_before:
            continue

        market_acts = act.get("market", [])
        animal_buys = [m for m in market_acts if m and m[0] == "BUY_ANIMAL"]
        if not animal_buys:
            continue

        farm = obs_before["farms"][seat]
        priv = obs_before.get("private") or {}
        shed = priv.get("shed") or {}

        # Shed non-seed items cannot exceed capacity (100)
        total_shed_items = sum(shed.values())
        assert total_shed_items < 100, f"Step {step_idx}: Bought animal when shed at capacity ({total_shed_items})"

        # Animals in shed + placed must not exceed farm capacity (max 4 per farm)
        total_animals = sum(shed.get(a, 0) for a in ("GOOSE", "COW", "SHEEP"))
        tiles = farm.get("tiles", [])
        for r in range(10):
            for c in range(10):
                tile = tiles[r][c]
                if isinstance(tile, dict) and tile.get("kind") in ("COOP", "PASTURE") and "animal" in tile:
                    total_animals += 1

        assert total_animals <= 4, (
            f"Step {step_idx}: Exceeded farm livestock capacity (Total animals={total_animals})"
        )
