from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

try:
    from controllers.base import MacroDecision
    from environment.encode import encode_state_1706
except ImportError:
    from controllers.base import MacroDecision
    from environment.encode import encode_state_1706

if TYPE_CHECKING:
    from environment.board import Board
    from environment.state import GameState

CROPS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON")


class NumPyMacroController:
    """Production-ready NumPy Macro Controller with safe path resolution."""

    def __init__(self, weights_path: Path | str | None = None) -> None:
        if weights_path is None:
            if "__file__" in globals():
                base_dir = Path(__file__).resolve().parents[1]
                weights_path = base_dir / "models" / "model_weights.npz"
            else:
                weights_path = Path("models/model_weights.npz")
            if not weights_path.exists():
                weights_path = Path("src/models/model_weights.npz")
            if not weights_path.exists():
                weights_path = Path("models/model_weights.npz")
            if not weights_path.exists():
                weights_path = Path("model_weights.npz")

        data = np.load(str(weights_path))
        self.w1 = data["w1"].astype(np.float32)
        self.b1 = data["b1"].astype(np.float32)
        self.w2 = data["w2"].astype(np.float32)
        self.b2 = data["b2"].astype(np.float32)
        self.w_out = data["w_out"].astype(np.float32)
        self.b_out = data["b_out"].astype(np.float32)

        self._last_decision: MacroDecision | None = None
        self._last_evaluated_day: int = -1

    def forward(self, features: np.ndarray) -> np.ndarray:
        h1 = np.maximum(0.0, np.dot(features, self.w1) + self.b1)
        h2 = np.maximum(0.0, np.dot(h1, self.w2) + self.b2)
        logits = np.dot(h2, self.w_out) + self.b_out
        exp_l = np.exp(logits - np.max(logits, axis=-1, keepdims=True))
        return exp_l / np.sum(exp_l, axis=-1, keepdims=True)

    def evaluate(self, state: GameState, board: Board) -> MacroDecision:
        day = state.step // 24
        if (
            self._last_decision is not None
            and day == self._last_evaluated_day
            and (state.step % 24 != 0)
        ):
            return self._last_decision

        features = encode_state_1706(state, board)
        probs = self.forward(features)[0]

        crop_probs = probs[0:5] / max(1e-8, float(np.sum(probs[0:5])))
        best_crop = CROPS[int(np.argmax(crop_probs))]
        target_crew = int(np.argmax(probs[5:16]))

        self._last_evaluated_day = day
        self._last_decision = MacroDecision(
            target_crop=best_crop,
            target_crew=target_crew,
            crop_distribution_bias=tuple(crop_probs.tolist()),
            market_reservation_scales={
                "MELON": float(probs[16] * 2.0),
                "STRAWBERRY": float(probs[17] * 2.0),
                "MILK": float(probs[18] * 2.0),
                "WOOL": float(probs[19] * 2.0),
            },
            should_expand_land=(day >= 8 and state.money >= 1000),
        )
        return self._last_decision

