from __future__ import annotations

__all__ = ["OPENING_TRACE"]

OPENING_TRACE: dict[int, dict] = {
    0: {
        "farmer": ["PASS"],
        "hands": [],
        "market": [
            ["HIRE"],
            ["HIRE"],
            ["HIRE"],
            ["HIRE"],
            ["HIRE"],
            ["BUY_ANIMAL", "SHEEP", 2],
            ["BUY_ANIMAL", "COW", 2],
            ["BUY_SEED", "WHEAT", 7],
            ["BUY_SEED", "MELON", 6],
            ["BUY_PRODUCT", "WHEAT", 8],
        ],
    },
    1: {
        "farmer": ["PICKUP", "COW", 2],
        "hands": [
            ["WEST"],
            ["NORTH"],
            ["PASS"],
            ["PICKUP", "SHEEP", 2],
            ["WEST"],
        ],
        "market": [["BUY_PRODUCT", "WHEAT", 2]],
    },
    2: {
        "farmer": ["BUILD_PASTURE"],
        "hands": [
            ["NORTH"],
            ["NORTH"],
            ["PASS"],
            ["PICKUP", "WHEAT", 2],
            ["NORTH"],
        ],
        "market": [],
    },
    3: {
        "farmer": ["PLACE", "COW"],
        "hands": [["NORTH"], ["NORTH"], ["PASS"], ["NORTH"], ["NORTH"]],
        "market": [],
    },
    4: {
        "farmer": ["WEST"],
        "hands": [
            ["BUILD_PASTURE"],
            ["NORTH"],
            ["PASS"],
            ["BUILD_PASTURE"],
            ["NORTH"],
        ],
        "market": [],
    },
    5: {
        "farmer": ["BUILD_PASTURE"],
        "hands": [
            ["WEST"],
            ["PLANT", "WHEAT"],
            ["PASS"],
            ["PLACE", "SHEEP"],
            ["NORTH"],
        ],
        "market": [],
    },
    6: {
        "farmer": ["PLACE", "COW"],
        "hands": [
            ["PLANT", "MELON"],
            ["WATER"],
            ["PASS"],
            ["FEED"],
            ["PLANT", "MELON"],
        ],
        "market": [],
    },
    7: {
        "farmer": ["WEST"],
        "hands": [["WATER"], ["WEST"], ["PASS"], ["CARE"], ["WATER"]],
        "market": [],
    },
    8: {
        "farmer": ["PLANT", "WHEAT"],
        "hands": [["WEST"], ["PLANT", "MELON"], ["PASS"], ["WEST"], ["WEST"]],
        "market": [],
    },
    9: {
        "farmer": ["WATER"],
        "hands": [
            ["PLANT", "WHEAT"],
            ["WATER"],
            ["PASS"],
            ["BUILD_PASTURE"],
            ["PLANT", "WHEAT"],
        ],
        "market": [],
    },
    10: {
        "farmer": ["PLANT", "WHEAT"],
        "hands": [["WATER"], ["WEST"], ["PASS"], ["PLACE", "SHEEP"], ["WATER"]],
        "market": [],
    },
    11: {
        "farmer": ["WATER"],
        "hands": [["WEST"], ["PLANT", "MELON"], ["PASS"], ["FEED"], ["WEST"]],
        "market": [],
    },
    12: {
        "farmer": ["WEST"],
        "hands": [
            ["PLANT", "MELON"],
            ["WATER"],
            ["PASS"],
            ["CARE"],
            ["PLANT", "MELON"],
        ],
        "market": [],
    },
    13: {
        "farmer": ["PLANT", "MELON"],
        "hands": [["WATER"], ["WEST"], ["PASS"], ["WEST"], ["WATER"]],
        "market": [],
    },
    14: {
        "farmer": ["WATER"],
        "hands": [
            ["WEST"],
            ["PLANT", "WHEAT"],
            ["PASS"],
            ["PLANT", "MELON"],
            ["WEST"],
        ],
        "market": [],
    },
    15: {
        "farmer": ["PASS"],
        "hands": [
            ["PLANT", "MELON"],
            ["WATER"],
            ["PASS"],
            ["WATER"],
            ["PLANT", "MELON"],
        ],
        "market": [],
    },
    16: {
        "farmer": ["PASS"],
        "hands": [["WATER"], ["WEST"], ["PASS"], ["WEST"], ["WATER"]],
        "market": [],
    },
    17: {
        "farmer": ["PASS"],
        "hands": [
            ["PASS"],
            ["PLANT", "MELON"],
            ["PASS"],
            ["PLANT", "WHEAT"],
            ["WEST"],
        ],
        "market": [],
    },
    18: {
        "farmer": ["PASS"],
        "hands": [["PASS"], ["WATER"], ["PASS"], ["WATER"], ["PLANT", "WHEAT"]],
        "market": [],
    },
    19: {
        "farmer": ["PASS"],
        "hands": [["PASS"], ["PASS"], ["PASS"], ["WEST"], ["WATER"]],
        "market": [],
    },
    20: {
        "farmer": ["PASS"],
        "hands": [["PASS"], ["PASS"], ["PASS"], ["PLANT", "MELON"], ["PASS"]],
        "market": [],
    },
    21: {
        "farmer": ["PASS"],
        "hands": [["PASS"], ["PASS"], ["PASS"], ["WATER"], ["PASS"]],
        "market": [],
    },
    22: {
        "farmer": ["PASS"],
        "hands": [["PASS"], ["PASS"], ["PASS"], ["PASS"], ["PASS"]],
        "market": [],
    },
    23: {
        "farmer": ["PASS"],
        "hands": [["PASS"], ["PASS"], ["PASS"], ["PASS"], ["PASS"]],
        "market": [],
    },
}
