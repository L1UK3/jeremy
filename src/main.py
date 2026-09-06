"""Kaggriculture agent entrypoint.

Combines neural macro economic policy with centralized spatial chore dispatching.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from dispatcher import schedule_tasks
from environment.board import Board
from environment.state import GameState
from model.policy import get_plan
from parameters import Parameters, get_active_parameters, use_parameters
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

__all__ = ["agent", "make_agent"]

_LAST_STEP: int = -1
_CLONE_CONFIDENCE: int = 0
_CURRENT_DAY: int = -1
_CURRENT_PLAN: dict[str, Any] | None = None


def make_agent(
    params: Parameters | None = None,
) -> Callable[[dict[str, Any]], dict[str, Any]]:
    """Factory creating an autonomous agent closure bound to specific Parameters."""
    configured_params = (
        params if params is not None else get_active_parameters()
    )

    def _agent(obs: dict[str, Any]) -> dict[str, Any]:
        with use_parameters(configured_params):
            return agent(obs)

    return _agent


def agent(obs: dict[str, Any]) -> dict[str, Any]:
    """Execute autonomous game turn via macro policy and spatial dispatcher."""
    global _LAST_STEP, _CLONE_CONFIDENCE, _CURRENT_DAY, _CURRENT_PLAN

    try:
        player = obs.get("player", 0)
        farms = obs.get("farms", [])
        hands_count = (
            len(farms[player].get("hands", []))
            if farms and len(farms) > player
            else 0
        )
    except Exception:
        hands_count = 0

    default_action: dict[str, Any] = {
        "farmer": ["PASS"],
        "hands": [["PASS"] for _ in range(hands_count)],
        "market": [],
    }

    try:
        params = get_active_parameters()
        state = GameState.from_obs(obs)
        board = Board(state)
        step = state.step
        day = state.day
        n_hands = len(state.hands)

        if step == 0 or step <= _LAST_STEP:
            _CLONE_CONFIDENCE = 0
            _CURRENT_DAY = -1
            _CURRENT_PLAN = None
        _LAST_STEP = step

        _CLONE_CONFIDENCE = update_clone_profile(
            obs, step, _CLONE_CONFIDENCE, params=params.clone_detector
        )

        # Terminal liquidation
        if step >= params.explosion.explosion_step:
            return explosion(state, board, params=params.explosion)

        action = {
            "farmer": ["PASS"],
            "hands": [["PASS"] for _ in range(n_hands)],
            "market": [],
        }
        pre_terminal_liquidation(action, state, step, params=params.explosion)

        # Stage 1: Macro Policy & Economic Strategy
        # Query macro plan on day boundaries
        if _CURRENT_PLAN is None or day != _CURRENT_DAY:
            _CURRENT_PLAN = get_plan(obs)
            _CURRENT_DAY = day
        plan = _CURRENT_PLAN or {}

        predation = str(plan.get("predation") or "Balanced")
        res_scales = adjust_reservation_scales(
            dict(plan.get("market") or {}),
            predation,
            params=params.predation,
        )

        # Procurement buy orders first
        market: list[list[Any]] = []
        target_crew = int(plan.get("crew", 0))
        target_animal = str(plan.get("livestock") or "NONE").upper()
        target_crop = str(plan.get("crop") or "WHEAT")

        apply_procurement(
            market,
            state,
            board,
            target_crop=target_crop,
            target_animal=target_animal,
            target_crew=target_crew,
            params=params.procurement,
        )

        # Market controller sell orders second
        action["market"] = market
        action = apply_market_controller(
            action,
            state,
            board,
            step,
            reservation_scales=res_scales,
            params=params.market_maker,
        )
        action = opening(action, step, params=params.debt_manager)

        market = list(action.get("market") or [])
        apply_predation(
            market, state, board, predation, params=params.predation
        )
        action["market"] = market[:10]
        action = filter_predation_sells(action, predation)

        # Stage 2: Unified Spatial Multi-Agent Dispatching
        farmer_act, hands_acts = schedule_tasks(
            state,
            board,
            target_crop=target_crop,
            params=params.dispatcher,
        )
        action["farmer"] = farmer_act
        action["hands"] = hands_acts

        # Post-dispatch reactive weed repair safety hooks
        action = weed_clear_state_based(
            state, board, action, params=params.weed_repair
        )
        action = weed_repair_productive_route(
            state, board, action, params=params.weed_repair
        )

        hands = [list(c) for c in (action.get("hands") or [])]
        if len(hands) < n_hands:
            hands.extend([["PASS"] for _ in range(n_hands - len(hands))])
        elif len(hands) > n_hands:
            hands = hands[:n_hands]

        return {
            "farmer": list(action.get("farmer") or ["PASS"]),
            "hands": hands,
            "market": [list(o) for o in (action.get("market") or [])][:10],
        }
    except Exception:
        return default_action
