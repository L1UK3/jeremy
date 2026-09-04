"""Jeremy V2 Main Agent Entrypoint with NumPy Macro Controller Integration."""

from __future__ import annotations

import copy
import logging
from typing import Any

from deprecated.controllers.numpy_macro import NumPyMacroController
from deprecated.environment.board import Board
from deprecated.environment.state import GameState
from deprecated.scheduler.dispatcher import _assign_one, generate_jobs
from deprecated.strategies.clone_detector import update_clone_profile
from deprecated.strategies.debt_manager import opening, repay, reset, split
from deprecated.strategies.explosion import explosion, pre_terminal_liquidation
from deprecated.strategies.front_runner import front_run
from deprecated.strategies.market_maker import apply_market_controller
from deprecated.strategies.weed_repair import (
    weed_repair_productive_route,
    weed_use_guarded,
)
from deprecated.trajectories.trace import FLAT_TRACE

__all__ = ["agent", "kaggle_submission_entrypoint"]

_MACRO_CONTROLLER: NumPyMacroController | None = None
_LAST_STEP: int = -1
_CLONE_CONFIDENCE: int = 0


def get_macro_controller() -> NumPyMacroController:
    """Lazy initialize NumPyMacroController instance."""
    global _MACRO_CONTROLLER
    if _MACRO_CONTROLLER is None:
        _MACRO_CONTROLLER = NumPyMacroController()
    return _MACRO_CONTROLLER


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
        controller = get_macro_controller()
        macro = controller.evaluate(state, board)
        action = copy.deepcopy(FLAT_TRACE[min(step, len(FLAT_TRACE) - 1)])
        front_run(action, state, step, FLAT_TRACE, _CLONE_CONFIDENCE)
        pre_terminal_liquidation(action, state, step)

        res_scales = macro.market_reservation_scales
        if macro.predation_mode == "FRONT_RUN":
            res_scales = {k: v * 0.85 for k, v in res_scales.items()}

        action = apply_market_controller(
            action,
            state,
            board,
            step,
            reservation_scales=res_scales,
        )
        action = weed_use_guarded(state, board, action, FLAT_TRACE)
        action = weed_repair_productive_route(state, board, action)
        _seat, debt_schedule = reset(state.player, step)
        due = debt_schedule.pop(step, {})
        action = repay(action, due)
        if due:
            carry = debt_schedule.setdefault(step + 1, {})
            for item, quantity in due.items():
                if quantity > 0:
                    carry[item] = carry.get(item, 0) + quantity
        action = opening(action, step)
        action = split(
            action, state, step, debt_schedule, FLAT_TRACE, _CLONE_CONFIDENCE
        )

        market = list(action.get("market") or [])
        if step >= 24 and len(market) < 10:
            if (
                len(state.hands) < macro.target_crew
                and state.money >= 100 * (len(state.hands) + 1)
                and not any(
                    isinstance(o, list) and o and o[0] == "HIRE" for o in market
                )
            ):
                market.append(["HIRE"])

            if (
                macro.target_animal != "NONE"
                and step >= 48
                and state.money >= 500
                and state.inventory("WHEAT") >= 2
                and not any(
                    isinstance(o, list) and o and o[0] == "BUY_ANIMAL"
                    for o in market
                )
            ):
                market.append(["BUY_ANIMAL", macro.target_animal, 1])

            if (
                macro.target_crop
                and state.seed_count(macro.target_crop) < 6
                and state.money >= 300
                and not any(
                    isinstance(o, list) and len(o) >= 2 and o[0] == "BUY_SEED"
                    for o in market
                )
            ):
                market.append(["BUY_SEED", macro.target_crop, 6])
        action["market"] = market[:10]

        hands = [list(c) for c in (action.get("hands") or [])]
        if len(hands) < n_hands:
            jobs = generate_jobs(
                state,
                board,
                target_crop=macro.target_crop,
                crop_weights=macro.crop_distribution_bias,
            )
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
