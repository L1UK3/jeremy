"""Pytest configuration and session-scoped Replay Provider fixtures."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

from simulation.episode import run_episode


@dataclass(slots=True)
class EpisodeTrace:
    """Encapsulates full-episode step observations and actions for invariant testing."""

    steps: list[list[dict[str, Any]]]
    seat: int
    source: str


def pytest_addoption(parser: pytest.Parser) -> None:
    """Register custom CLI options for replay-based testing."""
    parser.addoption(
        "--replay",
        action="store",
        default=None,
        help="Path to an existing episode replay (.html or .json) to evaluate invariants against.",
    )
    parser.addoption(
        "--seat",
        action="store",
        type=int,
        default=0,
        help="Challenger seat index (0 or 1, default: 0).",
    )


def load_replay_from_path(path: Path | str, seat: int = 0) -> EpisodeTrace:
    """Load steps from a Kaggle environment HTML or JSON replay file."""
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"Replay file not found: {p}")

    text = p.read_text(encoding="utf-8")
    if p.suffix.lower() == ".html" or "window.kaggle" in text:
        match = re.search(r"window\.kaggle\s*=\s*(\{.*\});", text, re.DOTALL)
        if not match:
            raise ValueError(f"Could not parse window.kaggle JSON from {p}")
        data = json.loads(match.group(1))
    else:
        data = json.loads(text)

    steps: list[list[dict[str, Any]]] = (
        data.get("environment", {}).get("steps") or data.get("steps") or []
    )
    if not steps:
        raise ValueError(f"Replay contains no step data: {p}")

    return EpisodeTrace(steps=steps, seat=seat, source=str(p))


@pytest.fixture(scope="session")
def episode_trace(request: pytest.FixtureRequest) -> EpisodeTrace:
    """Session-scoped fixture supplying episode steps from replay or live simulation."""
    replay_arg = request.config.getoption("--replay") or os.environ.get(
        "JEREMY_REPLAY_PATH"
    )
    seat_arg = request.config.getoption("--seat")

    if replay_arg:
        return load_replay_from_path(replay_arg, seat=seat_arg)

    # Fallback to headless 720-step simulation
    result = run_episode(
        challenger="src/main.py",
        baseline="starter",
        seat=seat_arg,
        steps=720,
        keep_env=True,
    )
    if not result.env or not result.env.steps:
        raise RuntimeError(
            "Headless episode execution failed to capture steps."
        )

    return EpisodeTrace(
        steps=result.env.steps,
        seat=seat_arg,
        source=f"headless_simulation_score_{result.score_challenger:.0f}",
    )
