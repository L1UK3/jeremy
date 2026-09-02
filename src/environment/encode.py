from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from environment.board import Board
    from environment.state import GameState

__all__ = ["encode_state_1706"]

# 10x10 board * 17 tile features (1700) + 6 global scalars = 1706 features
_FEATURE_BUFFER = np.zeros((1, 1706), dtype=np.float32)

CROP_INDEX = {"WHEAT": 1, "CARROT": 2, "TOMATO": 3, "STRAWBERRY": 4, "MELON": 5}
ANIMAL_INDEX = {"COW": 8, "SHEEP": 9, "GOOSE": 10}


def encode_state_1706(state: GameState, board: Board) -> np.ndarray:
    """Vectorize GameState and Board into [1, 1706] float32 vector in <0.2ms."""
    _FEATURE_BUFFER.fill(0.0)

    unlocked_set = state.unlocked_quadrants_set
    farmer_pos = state.farmer
    hands_set = {tuple(h) for h in state.hands}
    current_day = state.day

    # 1. Spatial Grid (17 features per tile x 100 tiles = 1700)
    idx = 0
    for r in range(10):
        for c in range(10):
            tile = board.tile(r, c)
            if tile.is_unlocked(unlocked_set):
                _FEATURE_BUFFER[0, idx + 0] = 1.0
            if tile.is_plant and tile.crop in CROP_INDEX:
                _FEATURE_BUFFER[0, idx + CROP_INDEX[tile.crop]] = 1.0
                _FEATURE_BUFFER[0, idx + 6] = float(tile.age(current_day)) / 10.0
                _FEATURE_BUFFER[0, idx + 7] = 1.0 if tile.watered else 0.0
            elif tile.is_animal and tile.animal in ANIMAL_INDEX:
                _FEATURE_BUFFER[0, idx + ANIMAL_INDEX[tile.animal]] = 1.0
            elif tile.is_weed:
                _FEATURE_BUFFER[0, idx + 11] = 1.0

            if (r, c) == farmer_pos:
                _FEATURE_BUFFER[0, idx + 13] = 1.0
            if (r, c) in hands_set:
                _FEATURE_BUFFER[0, idx + 14] = 1.0
            idx += 17

    # 2. Global Scalars (Indices 1700 to 1705)
    _FEATURE_BUFFER[0, 1700] = state.step / 720.0
    _FEATURE_BUFFER[0, 1701] = min(1.0, state.money / 10000.0)
    _FEATURE_BUFFER[0, 1702] = len(state.hands) / 10.0
    _FEATURE_BUFFER[0, 1703] = float(state.prices.get("MELON", 250)) / 500.0
    _FEATURE_BUFFER[0, 1704] = float(state.prices.get("STRAWBERRY", 120)) / 300.0
    _FEATURE_BUFFER[0, 1705] = float(state.prices.get("MILK", 160)) / 400.0

    return _FEATURE_BUFFER

