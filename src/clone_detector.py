"""Public farm fingerprinting and opponent clone detection for Jeremy V3."""

from __future__ import annotations

from typing import Any

__all__ = ["public_signature", "signature_distance", "update_clone_profile"]

SIGNATURE_ITEMS: tuple[str, ...] = (
    "COW",
    "SHEEP",
    "GOOSE",
    "WHEAT",
    "CARROT",
    "TOMATO",
    "STRAWBERRY",
    "MELON",
    "PASTURE",
    "COOP",
    "WEED",
)


def public_signature(
    farm: dict[str, Any],
) -> tuple[int, tuple[str, ...], tuple[tuple[int, int], ...], tuple[int, ...]]:
    """Compact public fingerprint for detecting a mirrored build."""
    counts: dict[str, int] = dict.fromkeys(SIGNATURE_ITEMS, 0)
    for row in farm.get("tiles", []) or []:
        for tile in row or []:
            if not isinstance(tile, dict):
                continue
            for key in ("animal", "crop", "kind"):
                value = tile.get(key)
                if value in counts:
                    counts[value] += 1
                    break
    positions = [farm.get("farmer", [0, 0]), *(farm.get("hands", []) or [])]
    return (
        len(farm.get("hands", []) or []),
        tuple(sorted(farm.get("unlocked_quadrants", []) or [])),
        tuple(sorted(tuple(position) for position in positions)),
        tuple(counts[item] for item in sorted(counts)),
    )


def signature_distance(
    left: tuple[int, tuple[str, ...], tuple[tuple[int, int], ...], tuple[int, ...]],
    right: tuple[int, tuple[str, ...], tuple[tuple[int, int], ...], tuple[int, ...]],
) -> int:
    """Compute distance metric between two public signatures."""
    distance = abs(left[0] - right[0])
    distance += 3 * abs(len(left[1]) - len(right[1]))
    distance += sum(abs(a - b) for a, b in zip(left[3], right[3], strict=False))
    if left[2] != right[2]:
        distance += 2
    return distance


def update_clone_profile(
    obs: dict[str, Any], step: int, current_confidence: int
) -> int:
    """Evaluate opponent farm similarity and return updated clone confidence."""
    if step not in (4, 24) and not (step >= 48 and step % 24 == 0):
        return current_confidence
    farms = obs.get("farms", []) or []
    if len(farms) < 2:
        return current_confidence
    player = int(obs.get("player", 0) or 0)
    distance = signature_distance(
        public_signature(farms[player]),
        public_signature(farms[1 - player]),
    )
    if distance <= 1:
        return min(8, current_confidence + 1)
    elif distance <= 4:
        return max(0, current_confidence - 1)
    else:
        return max(0, current_confidence - 3)
