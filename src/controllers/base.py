from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from environment.board import Board
    from environment.state import GameState

__all__ = ["MacroController", "MacroDecision"]


@dataclass(frozen=True, slots=True)
class MacroDecision:
    """Immutable macro-strategy recommendations for the current phase/day."""

    target_crop: str
    target_crew: int
    crop_distribution_bias: tuple[float, ...]
    market_reservation_scales: dict[str, float]
    should_expand_land: bool


class MacroController(Protocol):
    """Strategy protocol for macro decision controllers."""

    def evaluate(self, state: GameState, board: Board) -> MacroDecision: ...
