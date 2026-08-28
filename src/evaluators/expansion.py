from __future__ import annotations

from typing import Any

from controller import AgentController
from economy import Economy
from state import GameState

__all__ = ["evaluate_expansion"]


def evaluate_expansion(
    state: GameState,
    eco: Economy,
    controller: AgentController,
) -> list[Any] | None:
    """Evaluate purchasing adjacent land quadrants."""
    if not controller.expand_land:
        return None

    num_unlocked = len(state.unlocked_quadrants_set)
    max_quads = controller.get_max_quadrants(state)

    if num_unlocked >= max_quads:
        return None

    if num_unlocked == 1:
        if state.day < 8:
            return None
        if not eco.should_expand():
            return None

    elif num_unlocked == 2:
        if state.day < 22:
            return None
        if not eco.should_expand():
            return None

    else:
        return None

    if target := eco.next_quadrant_target():
        return ["BUY_LAND", target[0], target[1]]

    return None
