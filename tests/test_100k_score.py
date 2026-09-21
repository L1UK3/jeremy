"""Integration test verifying all four 100k Episode Invariants.

Top-level seam test via kaggle_environments asserting:
1. Final reward >= 100,000.
2. Livestock survival: zero animal starvation/escape events (consecutive_unfed < 2).
3. Land expansion: Quadrant 2 (NE) unlocked <= Day 9, Quadrant 3 (SW) unlocked <= Day 14.
4. Strawberry carpet: >= 30 active strawberry tiles during mid-season (Days 14-22).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tests.conftest import EpisodeTrace


def test_final_reward_invariant(episode_trace: EpisodeTrace) -> None:
    """Invariant 1: Total score >= 100,000 at turn 720 against simulation/base/main.py baseline."""
    seat = episode_trace.seat
    final_step = episode_trace.steps[-1]
    agent_record = final_step[seat]
    score = float(agent_record.get("reward") or 0.0)

    assert score >= 100_000, (
        f"Final reward {score:.0f} did not reach 100,000 benchmark threshold."
    )


def test_livestock_survival_invariant(episode_trace: EpisodeTrace) -> None:
    """Invariant 2: Zero animals starve or escape; consecutive_unfed < 2 across all 720 turns."""
    seat = episode_trace.seat
    steps = episode_trace.steps

    for step_idx, step_data in enumerate(steps):
        obs = step_data[seat].get("observation") or {}
        farms = obs.get("farms", [])
        if not farms or len(farms) <= seat:
            continue

        tiles = farms[seat].get("tiles", [])
        for r in range(len(tiles)):
            for c in range(len(tiles[r])):
                cell = tiles[r][c]
                if isinstance(cell, dict) and cell.get("kind") in ("COOP", "PASTURE"):
                    if cell.get("animal"):
                        unfed = cell.get("consecutive_unfed", 0)
                        assert unfed < 2, (
                            f"Step {step_idx} ({cell.get('animal')} at ({c}, {r})): "
                            f"consecutive_unfed reached {unfed} (animal starved/escaped)."
                        )


def test_land_expansion_timing_invariant(episode_trace: EpisodeTrace) -> None:
    """Invariant 3: Quadrant 2 (NE) unlocked by Day 9, Quadrant 3 (SW) unlocked by Day 14."""
    seat = episode_trace.seat
    steps = episode_trace.steps

    # Check Day 9 boundary (hour 0 of Day 9 is step 9 * 24)
    step_day9 = min(9 * 24, len(steps) - 1)
    obs_day9 = steps[step_day9][seat].get("observation") or {}
    quads_day9 = obs_day9.get("farms", [{}])[seat].get("unlocked_quadrants", [])
    assert "NE" in quads_day9, (
        f"Quadrant 2 (NE) was not unlocked by Day 9. Unlocked quadrants: {quads_day9}"
    )

    # Check Day 14 boundary (hour 0 of Day 14 is step 14 * 24)
    step_day14 = min(14 * 24, len(steps) - 1)
    obs_day14 = steps[step_day14][seat].get("observation") or {}
    quads_day14 = obs_day14.get("farms", [{}])[seat].get("unlocked_quadrants", [])
    assert "SW" in quads_day14, (
        f"Quadrant 3 (SW) was not unlocked by Day 14. Unlocked quadrants: {quads_day14}"
    )


def test_strawberry_carpet_invariant(episode_trace: EpisodeTrace) -> None:
    """Invariant 4: >= 30 active strawberry tiles present during mid-season (Days 14-22)."""
    seat = episode_trace.seat
    steps = episode_trace.steps

    for day in range(14, 23):
        step_idx = min(day * 24, len(steps) - 1)
        obs = steps[step_idx][seat].get("observation") or {}
        tiles = obs.get("farms", [{}])[seat].get("tiles", [])

        strawberry_count = 0
        for r in range(len(tiles)):
            for c in range(len(tiles[r])):
                cell = tiles[r][c]
                if (
                    isinstance(cell, dict)
                    and cell.get("kind") == "PLANT"
                    and cell.get("crop") == "STRAWBERRY"
                ):
                    strawberry_count += 1

        assert strawberry_count >= 30, (
            f"Day {day} (step {step_idx}): only {strawberry_count} active strawberry "
            f"tiles (expected >= 30)."
        )
