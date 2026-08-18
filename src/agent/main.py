"""
Main agent entrypoint.
Integrates the rule-based heuristics planner.
"""

from planner import Planner

from environment.state import GameState


def agent(obs: dict) -> dict:
    """Main agent callback for Kaggriculture."""
    state = GameState.from_obs(obs)
    planner = Planner(state)
    return planner.play().to_dict()
