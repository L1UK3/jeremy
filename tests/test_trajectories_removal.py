from __future__ import annotations

from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"


def test_trajectories_directory_does_not_exist() -> None:
    """The src/trajectories directory must be completely removed."""
    trajectories_dir = SRC / "trajectories"
    assert not trajectories_dir.exists(), f"{trajectories_dir} still exists on disk"


def test_no_references_to_trajectories_or_flat_trace_in_src() -> None:
    """No python file in src/ should reference 'trajectories' or 'FLAT_TRACE'."""
    violations: list[str] = []
    for py_file in SRC.rglob("*.py"):
        content = py_file.read_text(encoding="utf-8")
        if "from trajectories" in content or "import trajectories" in content:
            violations.append(f"{py_file.relative_to(ROOT)} imports trajectories")
        if "FLAT_TRACE" in content:
            violations.append(f"{py_file.relative_to(ROOT)} references FLAT_TRACE")

    assert not violations, f"Found trace references in src:\n" + "\n".join(violations)


def test_main_agent_runs_without_trace_dependencies() -> None:
    """main.agent(obs) must execute without trace dependencies or missing asset errors."""
    from main import agent

    obs: dict[str, Any] = {
        "player": 0,
        "step": 0,
        "day": 0,
        "hour": 0,
        "farms": [
            {
                "money": 3000,
                "tiles": [[None for _ in range(10)] for _ in range(10)],
                "farmer": [2, 2],
                "hands": [],
                "unlocked_quadrants": ["NW"],
                "hires_today": 0,
            },
            {
                "money": 3000,
                "tiles": [[None for _ in range(10)] for _ in range(10)],
                "farmer": [2, 2],
                "hands": [],
                "unlocked_quadrants": ["NW"],
                "hires_today": 0,
            },
        ],
        "private": {
            "shed": {},
            "seeds": {},
            "inventories": [[]],
        },
        "market": {
            "inventory": {
                "WHEAT": 800,
                "CARROT": 600,
                "TOMATO": 400,
                "STRAWBERRY": 200,
                "MELON": 150,
                "MILK": 150,
                "WOOL": 150,
            },
            "prices": {
                "WHEAT": 25,
                "CARROT": 35,
                "TOMATO": 60,
                "STRAWBERRY": 120,
                "MELON": 250,
                "MILK": 160,
                "WOOL": 200,
            },
        },
        "town": {
            "unlocked_shops": ["BAKERY"],
        },
    }

    action = agent(obs)
    assert isinstance(action, dict)
    assert "farmer" in action
    assert "hands" in action
    assert "market" in action
    assert isinstance(action["farmer"], list)
    assert isinstance(action["hands"], list)
    assert isinstance(action["market"], list)

