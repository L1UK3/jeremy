from __future__ import annotations

from typing import Any

from agent.planner import Planner
from environment.state import GameState

__all__ = ["agent"]


def agent(obs: dict[str, Any]) -> dict[str, Any]:
    """Main agent callback for Kaggriculture."""
    state = GameState.from_obs(obs)
    planner = Planner(state)
    return planner.play().to_dict()
