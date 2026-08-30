from __future__ import annotations

from src.board import Board
from src.scheduler import (
    Job,
    assign_jobs,
    default_utility_scorer,
    generate_jobs,
    job_to_action,
    schedule_tasks,
)
from src.state import GameState


def _mock_obs() -> dict:
    tiles: list[list[dict | str | None]] = [
        [None for _ in range(10)] for _ in range(10)
    ]
    # Harvestable crop at (0, 0)
    tiles[0][0] = {
        "kind": "PLANT",
        "crop": "MELON",
        "planted_day": 0,
        "watered_today": True,
        "yield_units": 4,
    }
    # Thirsty plant at (1, 1)
    tiles[1][1] = {
        "kind": "PLANT",
        "crop": "CARROT",
        "planted_day": 0,
        "watered_today": False,
        "yield_units": 0,
        "consecutive_unwatered": 1,
    }
    # Weed at (4, 4) in unlocked NW quadrant
    tiles[4][4] = {"kind": "WEED"}

    return {
        "player": 0,
        "step": 12 * 24,
        "day": 12,
        "hour": 0,
        "market": {"prices": {"WHEAT": 30, "CARROT": 40, "MELON": 200}},
        "farms": [
            {
                "money": 1000,
                "farmer": [0, 0],
                "hands": [[1, 1]],
                "unlocked_quadrants": ["NW"],
                "tiles": tiles,
            }
        ],
        "private": {"shed": {"WHEAT": 5}, "seeds": {"WHEAT": 3}},
    }


def test_job_and_utility():
    job = Job(priority=150.0, action="HARVEST", target=(0, 0), item="WHEAT")
    assert job.priority == 150.0
    assert default_utility_scorer(job, 0, 0) == 150.0
    assert default_utility_scorer(job, 1, 1) == 146.0

    # Underfoot action
    assert job_to_action(job, 0, 0) == ["HARVEST"]
    # Distance movement
    assert job_to_action(job, 2, 0) == ["WEST"]


def test_generate_and_assign_jobs():
    obs = _mock_obs()
    state = GameState.from_obs(obs)
    board = Board(state)

    jobs = generate_jobs(state, board, target_crop="WHEAT")
    assert len(jobs) >= 3

    # Check job types present
    actions = {j.action for j in jobs}
    assert "HARVEST" in actions
    assert "WATER" in actions
    assert "DIG" in actions

    # Assign jobs to farmer (at 0, 0) and farmhand (at 1, 1)
    farmer_act, hands_acts = assign_jobs(state, jobs)
    assert farmer_act == ["HARVEST"]
    assert hands_acts == [["WATER"]]


def test_schedule_tasks_pipeline():
    obs = _mock_obs()
    state = GameState.from_obs(obs)
    board = Board(state)

    farmer_act, hands_acts = schedule_tasks(state, board, target_crop="WHEAT")
    assert isinstance(farmer_act, list)
    assert isinstance(hands_acts, list)
    assert len(hands_acts) == 1
    assert farmer_act == ["HARVEST"]
    assert hands_acts[0] == ["WATER"]
