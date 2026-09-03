from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

from sample.controllers.base import MacroDecision
from sample.environment.encode import encode_state_1706

if TYPE_CHECKING:
    from sample.environment.board import Board
    from sample.environment.state import GameState

CROPS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON")
ANIMALS = ("NONE", "COW", "SHEEP", "GOOSE")
PREDATION_MODES = ("BALANCED", "FRONT_RUN", "CORNER_FEED")


class NumPyMacroController:
    """Production-ready NumPy Macro Controller with safe path resolution."""

    def __init__(self, weights_path: Path | str | None = None) -> None:
        if weights_path is None:
            candidates = (
                Path(__file__).resolve().parents[1]
                / "models"
                / "model_weights.npz"
                if "__file__" in globals()
                else None,
                Path("src/models/model_weights.npz"),
                Path("models/model_weights.npz"),
                Path("model_weights.npz"),
            )
            for p in candidates:
                if p and p.exists():
                    weights_path = p
                    break

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

        animal_probs = probs[20:24]
        target_animal = ANIMALS[int(np.argmax(animal_probs))]

        pred_probs = probs[24:27]
        predation_mode = PREDATION_MODES[int(np.argmax(pred_probs))]

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
            target_animal=target_animal,
            predation_mode=predation_mode,
        )
        return self._last_decision
