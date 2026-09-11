"""Episode invariant tests for Farm Hand hiring, budget discipline, and actions."""

from __future__ import annotations

from typing import TYPE_CHECKING

from strategies.procurement import FIBONACCI

if TYPE_CHECKING:
    from tests.conftest import EpisodeTrace

VALID_WORKER_OPS = frozenset(
    {
        "NORTH",
        "SOUTH",
        "EAST",
        "WEST",
        "PASS",
        "PLANT",
        "WATER",
        "HARVEST",
        "FERTILIZE",
        "BUILD_COOP",
        "BUILD_PASTURE",
        "FEED",
        "COLLECT_FERTILIZER",
        "CARE",
        "DIG",
        "PICKUP",
        "PLACE",
        "DROP",
    }
)


def test_daily_hire_count_within_limits(episode_trace: EpisodeTrace) -> None:
    """Agent must not exceed maximum daily hire cap (16 hires/day)."""
    seat = episode_trace.seat
    steps = episode_trace.steps

    daily_hires: dict[int, int] = {}
    for step_idx in range(1, len(steps)):
        act = steps[step_idx][seat].get("action") or {}
        obs_before = steps[step_idx - 1][seat].get("observation") or {}
        day = obs_before.get("day", (step_idx - 1) // 24)

        for m_act in act.get("market", []):
            if m_act and m_act[0] == "HIRE":
                daily_hires[day] = daily_hires.get(day, 0) + 1

    for day, hires in daily_hires.items():
        assert hires <= 16, f"Day {day} exceeded daily hire cap: {hires} hires"


def test_hires_affordability_discipline(episode_trace: EpisodeTrace) -> None:
    """Agent must hold sufficient capital for the Fibonacci hire cost when ordering HIRE."""
    seat = episode_trace.seat
    steps = episode_trace.steps

    for step_idx in range(1, len(steps)):
        act = steps[step_idx][seat].get("action") or {}
        obs_before = steps[step_idx - 1][seat].get("observation") or {}
        if not obs_before or "farms" not in obs_before:
            continue

        farm = obs_before["farms"][seat]
        money = farm.get("money", 0)
        hires_so_far = farm.get("hires_today", 0)

        hire_orders = [m for m in act.get("market", []) if m and m[0] == "HIRE"]
        for order_idx, _ in enumerate(hire_orders):
            hire_idx = hires_so_far + order_idx
            hire_cost = FIBONACCI[min(hire_idx, len(FIBONACCI) - 1)]
            assert money >= hire_cost, (
                f"Step {step_idx}: Emitted HIRE with insufficient funds "
                f"(Money=${money}, Required=${hire_cost} for hire #{hire_idx + 1})"
            )
            money -= hire_cost


def test_farm_hands_actions_validity(episode_trace: EpisodeTrace) -> None:
    """Farmer and Farm Hands must always emit recognized, valid game actions."""
    seat = episode_trace.seat
    steps = episode_trace.steps

    for step_idx, step_data in enumerate(steps):
        agent_step = step_data[seat]
        act = agent_step.get("action") or {}

        farmer_act = act.get("farmer", [])
        if farmer_act:
            assert farmer_act[0] in VALID_WORKER_OPS, (
                f"Step {step_idx}: Unknown farmer action {farmer_act}"
            )

        for h_idx, hand_act in enumerate(act.get("hands", [])):
            if hand_act:
                assert hand_act[0] in VALID_WORKER_OPS, (
                    f"Step {step_idx} Hand {h_idx}: Unknown action {hand_act}"
                )


def test_crew_scales_with_land_expansion(episode_trace: EpisodeTrace) -> None:
    """Crew size and hiring must scale proportionally with unlocked quadrants."""
    seat = episode_trace.seat
    steps = episode_trace.steps

    daily_quads: dict[int, int] = {}
    daily_hires: dict[int, int] = {}

    for step_idx, step_data in enumerate(steps):
        agent_step = step_data[seat]
        obs = agent_step.get("observation") or {}
        act = agent_step.get("action") or {}
        day = obs.get("day", step_idx // 24)

        if "farms" in obs:
            farm = obs["farms"][seat]
            quads = len(farm.get("unlocked_quadrants", ["NW"]))
            daily_quads[day] = max(daily_quads.get(day, 1), quads)

        for m_act in act.get("market", []):
            if m_act and m_act[0] == "HIRE":
                daily_hires[day] = daily_hires.get(day, 0) + 1

    for day, quads in daily_quads.items():
        if quads >= 2 and day < 28:
            hires = daily_hires.get(day, 0)
            assert hires >= 2, (
                f"Day {day} with {quads} unlocked quadrants hired only {hires} hands"
            )
