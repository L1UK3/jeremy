"""Jeremy V3 Main Agent Entrypoint with Dynamic Scheduler Integration."""

from __future__ import annotations

import copy
import logging
from trace import FLAT_TRACE
from typing import Any

from board import Board
from clone_detector import update_clone_profile
from debt_manager import c94_opening, c94_repay, c94_reset, c94_split
from explosion import explosion, pre_terminal_liquidation
from front_runner import front_run
from market_maker import apply_market_controller
from scheduler import _assign_one, generate_jobs
from state import GameState
from weed_repair import weed_repair_productive_route, weed_use_guarded

__all__ = ["agent", "kaggle_submission_entrypoint"]

_LAST_STEP: int = -1
_CLONE_CONFIDENCE: int = 0


def agent(obs: dict[str, Any]) -> dict[str, Any]:
    """Execute full closed-loop reactive agent decision pipeline."""
    global _LAST_STEP, _CLONE_CONFIDENCE

    state = GameState.from_obs(obs)
    board = Board(state)
    step = state.step
    n_hands = len(state.hands)

    if step == 0 or step <= _LAST_STEP:
        _CLONE_CONFIDENCE = 0
    _LAST_STEP = step

    _CLONE_CONFIDENCE = update_clone_profile(obs, step, _CLONE_CONFIDENCE)

    if step >= 712:
        return explosion(state, board)

    try:
        action = copy.deepcopy(FLAT_TRACE[min(step, len(FLAT_TRACE) - 1)])
        front_run(action, state, step, FLAT_TRACE, _CLONE_CONFIDENCE)
        pre_terminal_liquidation(action, state, step)
        action = apply_market_controller(action, state, board, step)
        action = weed_use_guarded(state, board, action, FLAT_TRACE)
        action = weed_repair_productive_route(state, board, action)
        _seat, debt_schedule = c94_reset(state.player, step)
        due = debt_schedule.pop(step, {})
        action = c94_repay(action, due)
        if due:
            carry = debt_schedule.setdefault(step + 1, {})
            for item, quantity in due.items():
                if quantity > 0:
                    carry[item] = carry.get(item, 0) + quantity
        action = c94_opening(action, step)
        action = c94_split(
            action, state, step, debt_schedule, FLAT_TRACE, _CLONE_CONFIDENCE
        )

        # Dynamic Extra Hand Dispatch via Scheduler
        hands = [list(c) for c in (action.get("hands") or [])]
        if len(hands) < n_hands:
            jobs = generate_jobs(state, board)
            used_targets: set[tuple[int, int]] = set()

            while len(hands) < n_hands:
                h_idx = len(hands)
                pos = tuple(state.hands[h_idx])
                assigned = _assign_one(
                    jobs, pos[0], pos[1], used_targets, state=state, board=board
                )
                hands.append(assigned)

        return {
            "farmer": list(action.get("farmer") or ["PASS"]),
            "hands": hands[:n_hands],
            "market": [list(o) for o in (action.get("market") or [])][:10],
        }
    except Exception as e:
        logging.error(f"Error in agent step {step}: {e}")
        return {
            "farmer": ["PASS"],
            "hands": [["PASS"] for _ in range(n_hands)],
            "market": [],
        }


def kaggle_submission_entrypoint(obs: dict[str, Any]) -> dict[str, Any]:
    """Standard Kaggle competition entrypoint wrapper."""
    return agent(obs)
