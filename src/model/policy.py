from pathlib import Path
from typing import Any

import numpy as np

from .constants import CROPS, LIVESTOCK, PREDATION_MODES
from .encoder import encode_observation

if "__file__" in globals():
    DEFAULT_WEIGHTS_PATH = Path(__file__).resolve().parent / "model_weights.npz"
else:
    DEFAULT_WEIGHTS_PATH = (
        Path.cwd() / "src" / "agent" / "model" / "model_weights.npz"
    )
    if not DEFAULT_WEIGHTS_PATH.exists():
        DEFAULT_WEIGHTS_PATH = Path("model_weights.npz")

with np.load(DEFAULT_WEIGHTS_PATH) as _data:
    _W1, _B1 = _data["w1"], _data["b1"]
    _W2, _B2 = _data["w2"], _data["b2"]
    _W_OUT, _B_OUT = _data["w_out"], _data["b_out"]

_cached_day: int = -1
_cached_plan: dict[str, Any] | None = None

CROP_NAMES: tuple[str, ...] = tuple(CROPS)
LIVESTOCK_NAMES: tuple[str, ...] = tuple(LIVESTOCK)
MARKET_ITEMS: tuple[str, ...] = ("MELON", "STRAWBERRY", "MILK", "WOOL")


def forward(features: np.ndarray) -> np.ndarray:
    h1: np.ndarray = np.maximum(0.0, np.dot(features, _W1) + _B1)
    h2: np.ndarray = np.maximum(0.0, np.dot(h1, _W2) + _B2)
    return np.dot(h2, _W_OUT) + _B_OUT


def get_plan(obs: dict[str, Any]) -> dict[str, Any]:
    global _cached_day, _cached_plan

    step: int = obs.get("step", 0)
    day: int = obs["day"]
    if step == 0:
        _cached_day = -1
        _cached_plan = None

    if _cached_plan is None or day != _cached_day:
        features: np.ndarray = encode_observation(obs)
        logits: np.ndarray = forward(features)[0]
        _cached_day = day
        _cached_plan = {
            "crop": CROP_NAMES[int(np.argmax(logits[0:5]))],
            "crew": int(np.argmax(logits[5:16])),
            "market": {
                k: max(0.0, min(2.0, float(logits[16 + i] * 2.0)))
                for i, k in enumerate(MARKET_ITEMS)
            },
            "livestock": LIVESTOCK_NAMES[int(np.argmax(logits[20:24]))],
            "predation": PREDATION_MODES[int(np.argmax(logits[24:27]))],
        }
    return _cached_plan


__all__ = ["get_plan"]
