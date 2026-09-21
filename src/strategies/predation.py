"""Opponent interaction and market predation strategies."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from parameters import PredationParams, get_active_parameters

if TYPE_CHECKING:
    from environment.board import Board
    from environment.state import GameState

__all__ = [
    "adjust_reservation_scales",
    "apply_predation",
    "filter_predation_sells",
]


def opponent_has_livestock(state: GameState) -> bool:
    """Inspect public tiles to detect if opponent is raising animals."""
    farms = state.raw.get("farms") or []
    if len(farms) < 2:
        return False
    opp_tiles = farms[1 - state.player].get("tiles") or []
    for row in opp_tiles:
        for tile in row:
            if isinstance(tile, dict) and (
                tile.get("animal") or tile.get("kind") in ("COOP", "PASTURE")
            ):
                return True
    return False


def apply_predation(
    market: list[list[Any]],
    state: GameState,
    board: Board,
    predation_mode: str,
    params: PredationParams | None = None,
) -> None:
    """Execute active predatory order logic."""
    pp = params or get_active_parameters().predation
    mode = predation_mode.lower()
    n_animals = len(board.animals())

    if "corner" in mode and len(market) < 10:
        # Choke market wheat supply if opponent has animals relying on feed
        if opponent_has_livestock(state):
            wheat_price = state.price("WHEAT") or 25
            qty = pp.corner_wheat_buy_qty
            if state.can_afford(wheat_price * qty):
                market.append(["BUY_PRODUCT", "WHEAT", qty])
    else:
        total_animals = (
            n_animals
            + sum(state.inventory(a) for a in ("GOOSE", "COW", "SHEEP"))
        )
        feed_buffer = max(18, total_animals * 3) if (total_animals > 0 or state.day < 10) else 0
        surplus_wheat = state.inventory("WHEAT") - feed_buffer
        if surplus_wheat > 0 and len(market) < 10:
            market.append(["SELL", "WHEAT", min(100, surplus_wheat)])


def adjust_reservation_scales(
    reservation_scales: dict[str, float],
    predation_mode: str,
    params: PredationParams | None = None,
) -> dict[str, float]:
    """Discount reservation sell price to front-run competitor produce when aggressive."""
    pp = params or get_active_parameters().predation
    if "front" in predation_mode.lower():
        return {
            k: v * pp.front_run_discount for k, v in reservation_scales.items()
        }
    return reservation_scales


def filter_predation_sells(
    action: dict[str, Any],
    predation_mode: str,
) -> dict[str, Any]:
    """Ensure hoarded resources (e.g. Wheat under Corner-feed) are not sold on market."""
    if "corner" in predation_mode.lower():
        action["market"] = [
            order
            for order in action.get("market") or []
            if not (
                isinstance(order, list)
                and len(order) >= 2
                and order[0] == "SELL"
                and order[1] == "WHEAT"
            )
        ][:10]
    return action
