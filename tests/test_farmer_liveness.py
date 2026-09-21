"""Integration test verifying Farmer Liveness Episode Invariant.

Executes 720-step episodes and asserts:
1. Farmer non-PASS action ratio >= 85% across the full episode.
2. Zero consecutive daytime PASS streaks > 3 turns while actionable field chores
   (unwatered or harvestable crops) exist.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tests.conftest import EpisodeTrace


def test_farmer_liveness_action_ratio(episode_trace: EpisodeTrace) -> None:
    """Farmer maintains continuous activity with non-PASS action ratio >= 85%."""
    seat = episode_trace.seat
    steps = episode_trace.steps

    non_pass_count = 0
    total_steps = 0

    for step_data in steps:
        agent_data = step_data[seat]
        act = agent_data.get("action")
        if act is None:
            continue
        total_steps += 1
        farmer_act = act.get("farmer", ["PASS"])
        if farmer_act != ["PASS"]:
            non_pass_count += 1

    assert total_steps > 0, "Episode contained no valid steps."
    ratio = non_pass_count / total_steps
    assert ratio >= 0.85, (
        f"Farmer non-PASS action ratio was {ratio:.2%} ({non_pass_count}/{total_steps}), "
        f"expected >= 85%."
    )


def test_no_unexplained_daytime_pass_streaks(episode_trace: EpisodeTrace) -> None:
    """Farmer has no consecutive daytime PASS streaks > 3 turns while actionable chores exist."""
    seat = episode_trace.seat
    steps = episode_trace.steps

    consecutive_pass = 0

    for step_idx, step_data in enumerate(steps):
        agent_data = step_data[seat]
        obs = agent_data.get("observation") or {}
        act = agent_data.get("action") or {}
        farmer_act = act.get("farmer", ["PASS"])

        farms = obs.get("farms", [])
        if not farms or len(farms) <= seat:
            continue

        my_farm = farms[seat]
        tiles = my_farm.get("tiles", [])

        # Check if actionable field chores exist (unwatered crops or harvestable crops)
        has_actionable_chore = False
        for r in range(len(tiles)):
            for c in range(len(tiles[r])):
                cell = tiles[r][c]
                if isinstance(cell, dict) and cell.get("kind") == "PLANT":
                    # Unwatered plant today
                    if not cell.get("watered_today", True):
                        has_actionable_chore = True
                        break
                    # Harvestable plant
                    if cell.get("yield_units", 0) > 0:
                        has_actionable_chore = True
                        break
            if has_actionable_chore:
                break

        if has_actionable_chore and farmer_act == ["PASS"]:
            consecutive_pass += 1
            assert consecutive_pass <= 3, (
                f"Step {step_idx} (day {obs.get('day')}, hour {obs.get('hour')}): "
                f"Farmer experienced consecutive PASS streak of {consecutive_pass} "
                f"while actionable field chores existed."
            )
        else:
            consecutive_pass = 0
