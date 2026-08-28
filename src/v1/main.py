from __future__ import annotations

from typing import Any

from actions import Action
from board import Board
from controller import AgentController
from economy import Economy
from evaluators import (
    evaluate_expansion,
    evaluate_livestock,
    evaluate_market,
)
from expansion import EXPANSION_TRACE
from explosion import explosion
from market import Market
from opening import OPENING_TRACE
from scheduler import Scheduler
from state import GameState

__all__ = ["agent"]

CONTROLLER = AgentController()


def agent(obs: dict[str, Any]) -> dict[str, Any]:
    """Main agent callback for Kaggriculture."""
    state = GameState.from_obs(obs)
    board = Board(state)
    eco = Economy(state)
    market = Market(state)
    scheduler = Scheduler(state)

    step = state.step

    # turns 0-23
    if step in OPENING_TRACE:
        act = OPENING_TRACE[step]
        return Action(
            farmer=act.get("farmer", ["PASS"]),
            hands=act.get("hands", []),
            market=act.get("market", []),
        ).to_dict()

    if step in EXPANSION_TRACE:
        act = EXPANSION_TRACE[step]
        return Action(
            farmer=act.get("farmer", ["PASS"]),
            hands=act.get("hands", []),
            market=act.get("market", []),
        ).to_dict()

    # turns 712-719
    if step >= (712):
        return explosion(state, board).to_dict()

    crop = CONTROLLER.get_crop(eco)
    market_orders = evaluate_market(state, board, eco, market, CONTROLLER, crop)

    if expansion_order := evaluate_expansion(state, eco, CONTROLLER):
        if len(market_orders) < 10:
            market_orders.append(expansion_order)

    livestock_act = evaluate_livestock(
        state, board, worker_idx=0, worker_pos=state.farmer
    )

    scheduler.populate(board, eco, crop)
    default_farmer_act, hands_acts = scheduler.assign()

    farmer_act = (
        livestock_act if livestock_act is not None else default_farmer_act
    )

    return Action(
        farmer=farmer_act,
        hands=hands_acts,
        market=market_orders,
    ).to_dict()
