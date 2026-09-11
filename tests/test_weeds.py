"""Episode invariant tests for weed management, crop protection, and DIG repairs."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

if TYPE_CHECKING:
    from tests.conftest import EpisodeTrace


def test_crop_rot_prevention(episode_trace: EpisodeTrace) -> None:
    """Cultivated crops must not turn into weeds due to unwatered neglect (consecutive_unwatered >= 2)."""
    seat = episode_trace.seat
    steps = episode_trace.steps

    neglect_weed_deaths: list[str] = []

    for step_idx in range(1, len(steps)):
        prev_obs = steps[step_idx - 1][seat].get("observation") or {}
        curr_obs = steps[step_idx][seat].get("observation") or {}
        if not prev_obs or not curr_obs or "farms" not in prev_obs:
            continue

        prev_tiles = prev_obs["farms"][seat].get("tiles", [])
        curr_tiles = curr_obs["farms"][seat].get("tiles", [])

        for r in range(10):
            for c in range(10):
                pt = prev_tiles[r][c]
                ct = curr_tiles[r][c]

                prev_is_plant = (
                    isinstance(pt, dict) and pt.get("kind") == "PLANT"
                )
                curr_is_weed = ct == "WEED" or (
                    isinstance(ct, dict) and ct.get("kind") == "WEED"
                )

                if prev_is_plant and curr_is_weed:
                    # Check if the plant was rotted due to 2+ consecutive unwatered days
                    unwatered = pt.get("consecutive_unwatered", 0)
                    if unwatered >= 2:
                        neglect_weed_deaths.append(
                            f"Step {step_idx} at ({r},{c}): Plant {pt.get('crop')} rotted "
                            f"to weed after {unwatered} unwatered days."
                        )

    assert not neglect_weed_deaths, (
        f"Found {len(neglect_weed_deaths)} crop neglect rot events:\n"
        + "\n".join(neglect_weed_deaths[:10])
    )


def test_weed_clearing_activity(episode_trace: EpisodeTrace) -> None:
    """If weeds appear on unlocked tiles, the agent must schedule DIG actions."""
    seat = episode_trace.seat
    steps = episode_trace.steps

    weed_spawn_detected = False
    dig_actions_count = 0

    for step_data in steps:
        agent_step = step_data[seat]
        obs = agent_step.get("observation") or {}
        act = agent_step.get("action") or {}
        if not obs or "farms" not in obs:
            continue

        tiles = obs["farms"][seat].get("tiles", [])
        for r in range(10):
            for c in range(10):
                t = tiles[r][c]
                if t == "WEED" or (
                    isinstance(t, dict) and t.get("kind") == "WEED"
                ):
                    weed_spawn_detected = True
                    break

        all_acts: list[list[Any]] = [
            act.get("farmer", []),
            *act.get("hands", []),
        ]
        for a in all_acts:
            if a and a[0] == "DIG":
                dig_actions_count += 1

    if weed_spawn_detected:
        assert dig_actions_count > 0, (
            "Weeds spawned on the farm during the episode, but the agent never executed a DIG action."
        )


def test_no_blocked_actions_on_weeds(episode_trace: EpisodeTrace) -> None:
    """Units standing on a weed must not attempt weed-blocked actions without digging."""
    seat = episode_trace.seat
    steps = episode_trace.steps
    blocked_ops = frozenset({"BUILD_PASTURE", "BUILD_COOP", "PLANT", "PLACE"})

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
            x, y = pos
            tile = tiles[y][x]
            is_weed = tile == "WEED" or (
                isinstance(tile, dict) and tile.get("kind") == "WEED"
            )
            if is_weed and a[0] in blocked_ops:
                pytest.fail(
                    f"Step {step_idx} Unit {idx} at ({x},{y}) attempted weed-blocked operation "
                    f"'{a[0]}' while standing on a weed."
                )
