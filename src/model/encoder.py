"""Vectorized feature encoder converting game observations to model tensors."""

from typing import Any

import numpy as np

from .constants import CROPS, LIVESTOCK, QUAD_BOUNDS


def encode_observation(obs: dict[str, Any]) -> np.ndarray:
    buf = np.zeros((1, 1706), dtype=np.float32)
    player = obs.get("player", 0)
    farm = obs["farms"][player]
    day = obs.get("day", 0)


    # Unlocked quadrants
    for q in farm.get("unlocked_quadrants", ("NW",)):
        r0, r1, c0, c1 = QUAD_BOUNDS[q]
        for r in range(r0, r1):
            buf[0, (r * 10 + c0) * 17 : (r * 10 + c1) * 17 : 17] = 1.0

    # Tiles (Plants, Animals, Weeds)
    tiles = farm["tiles"]
    for r in range(10):
        row = tiles[r]
        r_offset = r * 170
        for c in range(10):
            t = row[c]
            if not isinstance(t, dict):
                continue
            idx = r_offset + c * 17
            kind = t.get("kind")
            if kind == "PLANT":
                crop = t.get("crop")
                if crop in CROPS:
                    buf[0, idx + CROPS[crop]] = 1.0
                    buf[0, idx + 6] = (day - t.get("planted_day", day)) / 10.0
                    buf[0, idx + 7] = 1.0 if t.get("watered_today") else 0.0
            elif kind == "WEED":
                buf[0, idx + 11] = 1.0
            else:
                anim_idx = LIVESTOCK.get(t.get("animal"))
                if anim_idx is not None:
                    buf[0, idx + anim_idx] = 1.0

    # Unit positions
    hands = farm.get("hands", ())
    fx, fy = farm["farmer"]
    buf[0, (fy * 10 + fx) * 17 + 13] = 1.0
    for hx, hy in hands:
        buf[0, (hy * 10 + hx) * 17 + 14] = 1.0

    # Global market and economic scalars
    prices = obs["market"]["prices"]
    step_val = obs.get("step", day * 24 + obs.get("hour", 0))
    buf[0, 1700] = float(step_val) / 720.0

    buf[0, 1701] = min(1.0, farm["money"] / 10000.0)
    buf[0, 1702] = len(hands) / 10.0
    buf[0, 1703] = prices.get("MELON", 250) / 500.0
    buf[0, 1704] = prices.get("STRAWBERRY", 120) / 300.0
    buf[0, 1705] = prices.get("MILK", 160) / 400.0

    return buf


__all__ = ["encode_observation"]
