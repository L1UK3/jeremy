"""Domain vocabulary and spatial indexing constants for Kaggriculture."""

CROPS: dict[str, int] = {
    "WHEAT": 1,
    "CARROT": 2,
    "TOMATO": 3,
    "STRAWBERRY": 4,
    "MELON": 5,
}

LIVESTOCK: dict[str, int | None] = {
    "NONE": None,
    "COW": 8,
    "SHEEP": 9,
    "GOOSE": 10,
}

PREDATION_MODES: tuple[str, ...] = ("Balanced", "Front-run", "Corner-feed")

QUAD_BOUNDS: dict[str, tuple[int, int, int, int]] = {
    "NW": (0, 5, 0, 5),
    "NE": (0, 5, 5, 10),
    "SW": (5, 10, 0, 5),
    "SE": (5, 10, 5, 10),
}

__all__ = [
    "CROPS",
    "LIVESTOCK",
    "PREDATION_MODES",
    "QUAD_BOUNDS",
]
