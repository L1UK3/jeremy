from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from board import Board
from economy import Economy
from evaluators import (
    evaluate_expansion,
    evaluate_livestock,
    evaluate_market,
)
from explosion import explosion
from market import Market
from scheduler import Scheduler
from state import GameState

__all__ = [
    "ROUTES",
    "agent",
    "expansion_agent",
    "explosion_agent",
    "main_agent",
    "opening_agent",
]


def _load_routes() -> dict[int, dict]:
    candidates = []
    if "__file__" in globals():
        candidates.append(Path(__file__).resolve().parent / "routes.json")
    candidates.extend(
        [
            Path("src/routes.json"),
            Path("routes.json"),
            Path(".out/routes.json"),
        ]
    )
    for path in candidates:
        if path.exists():
            with open(path, encoding="utf-8") as f:
                raw = json.load(f)
            return {int(k): v for k, v in raw.items()}
    return {}


ROUTES: dict[int, dict] = _load_routes()


def opening_agent(
    obs: dict[str, Any],
    state: GameState | None = None,
) -> dict[str, Any]:
    """Opening phase agent (turns 0-23) executing scripted high-yield trajectories."""
    if state is None:
        state = GameState.from_obs(obs)
    step = state.step
    if step in ROUTES:
        act = ROUTES[step]
        return {
            "farmer": act.get("farmer", ["PASS"]),
            "hands": act.get("hands", []),
            "market": act.get("market", []),
        }
    return main_agent(obs, state=state)


def expansion_agent(
    obs: dict[str, Any],
    state: GameState | None = None,
) -> dict[str, Any]:
    """Expansion phase agent executing quadrant expansion trajectories."""
    if state is None:
        state = GameState.from_obs(obs)
    step = state.step
    if step in ROUTES:
        act = ROUTES[step]
        return {
            "farmer": act.get("farmer", ["PASS"]),
            "hands": act.get("hands", []),
            "market": act.get("market", []),
        }
    return main_agent(obs, state=state)


def explosion_agent(
    obs: dict[str, Any],
    state: GameState | None = None,
    board: Board | None = None,
) -> dict[str, Any]:
    """Final 8-turn liquidation agent (turns 712-719)."""
    if state is None:
        state = GameState.from_obs(obs)
    if board is None:
        board = Board(state)
    return explosion(state, board)


def main_agent(
    obs: dict[str, Any],
    state: GameState | None = None,
    board: Board | None = None,
    eco: Economy | None = None,
    market: Market | None = None,
    scheduler: Scheduler | None = None,
) -> dict[str, Any]:
    """Dynamic mid-game agent managing crops, livestock, market, and scheduling."""
    if state is None:
        state = GameState.from_obs(obs)
    if board is None:
        board = Board(state)
    if eco is None:
        eco = Economy(state)
    if market is None:
        market = Market(state)
    if scheduler is None:
        scheduler = Scheduler(state)

    crop = eco.best_crop()
    market_orders = evaluate_market(state, board, eco, market, crop)

    if expansion_order := evaluate_expansion(state, eco):
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

    if len(board.needs_feed()) > 0 and len(state.hands) > 0:
        for h_idx, h_pos in enumerate(state.hands, start=1):
            hand_pos = (h_pos[0], h_pos[1])
            hand_livestock = evaluate_livestock(
                state, board, worker_idx=h_idx, worker_pos=hand_pos
            )
            if hand_livestock is not None:
                hands_acts[h_idx - 1] = hand_livestock
                break

    return {
        "farmer": farmer_act,
        "hands": hands_acts,
        "market": market_orders,
    }


def agent(obs: dict[str, Any]) -> dict[str, Any]:
    """Agent wrapper routing turns to specialized phase agents."""
    state = GameState.from_obs(obs)
    step = state.step

    # Opening phase (turns 0-23)
    if step < 24:
        return opening_agent(obs, state=state)

    # Endgame liquidation (turns 712-719)
    if step >= 712:
        return explosion_agent(obs, state=state)

    # Scripted expansion phases (turns 169-192, 265-288)
    if step in ROUTES:
        return expansion_agent(obs, state=state)

    # Dynamic mid-game operations
    return main_agent(obs, state=state)
