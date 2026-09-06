"""Kaggriculture agent entrypoint combining macro policy with spatial chore dispatching."""

from __future__ import annotations

from typing import Any

from dispatcher import _assign_one, generate_jobs
from environment.board import Board
from environment.state import GameState
from model.policy import get_plan
from strategies import (
    adjust_reservation_scales,
    apply_market_controller,
    apply_predation,
    apply_procurement,
    explosion,
    filter_predation_sells,
    opening,
    pre_terminal_liquidation,
    update_clone_profile,
    weed_clear_state_based,
    weed_repair_productive_route,
)

__all__ = ["agent"]

_LAST_STEP: int = -1
_CLONE_CONFIDENCE: int = 0


def agent(obs: dict[str, Any]) -> dict[str, Any]:
    """Execute autonomous game turn via macro policy and reactive strategies."""
    global _LAST_STEP, _CLONE_CONFIDENCE

    state = GameState.from_obs(obs)
    board = Board(state)
    step = state.step
    n_hands = len(state.hands)

    default_action: dict[str, Any] = {
        "farmer": ["PASS"],
        "hands": [["PASS"] for _ in range(n_hands)],
        "market": [],
    }

    if step == 0 or step <= _LAST_STEP:
        _CLONE_CONFIDENCE = 0
    _LAST_STEP = step

    _CLONE_CONFIDENCE = update_clone_profile(obs, step, _CLONE_CONFIDENCE)

    # Terminal 8-turn liquidation
    if step >= 712:
        return explosion(state, board)

    try:
        action = default_action.copy()
        pre_terminal_liquidation(action, state, step)
        plan = get_plan(obs)
        predation = str(plan.get("predation") or "Balanced")
        res_scales = adjust_reservation_scales(
            dict(plan.get("market") or {}),
            predation,
        )
        action = apply_market_controller(
            action,
            state,
            board,
            step,
            reservation_scales=res_scales,
        )
        action = weed_clear_state_based(state, board, action)
        action = weed_repair_productive_route(state, board, action)
        action = opening(action, step)

        market = list(action.get("market") or [])
        target_crew = int(plan.get("crew", 0))
        target_animal = str(plan.get("livestock") or "NONE").upper()
        target_crop = str(plan.get("crop") or "WHEAT")

        if step >= 24:
            apply_procurement(
                market,
                state,
                board,
                target_crop=target_crop,
                target_animal=target_animal,
                target_crew=target_crew,
            )
        apply_predation(market, state, board, predation)
        action["market"] = market[:10]
        action = filter_predation_sells(action, predation)

        hands = [list(c) for c in (action.get("hands") or [])]
        if len(hands) < n_hands:
            jobs = generate_jobs(
                state,
                board,
                target_crop=target_crop,
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
    except Exception:
        return default_action
