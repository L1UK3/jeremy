from __future__ import annotations

OPENING_TRACE: dict[int, dict] = {
    1: {
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
            ["BUY_SEED", "MELON", 12],
        ],
    },
    2: {
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
    3: {
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
    4: {
        "farmer": ["PLACE", "COW"],
        "hands": [["NORTH"], ["NORTH"], ["PASS"], ["NORTH"], ["NORTH"]],
        "market": [],
    },
    5: {
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
    6: {
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
    7: {
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
    8: {
        "farmer": ["WEST"],
        "hands": [["WATER"], ["WEST"], ["PASS"], ["CARE"], ["WATER"]],
        "market": [],
    },
    9: {
        "farmer": ["BUILD_PASTURE"],
        "hands": [["WEST"], ["PLANT", "MELON"], ["PASS"], ["WEST"], ["WEST"]],
        "market": [],
    },
    10: {
        "farmer": ["WEST"],
        "hands": [
            ["PLANT", "WHEAT"],
            ["WATER"],
            ["PASS"],
            ["BUILD_PASTURE"],
            ["PLANT", "WHEAT"],
        ],
        "market": [],
    },
    11: {
        "farmer": ["PLANT", "WHEAT"],
        "hands": [["WATER"], ["WEST"], ["PASS"], ["PLACE", "SHEEP"], ["WATER"]],
        "market": [],
    },
    12: {
        "farmer": ["WATER"],
        "hands": [["WEST"], ["PLANT", "MELON"], ["PASS"], ["FEED"], ["WEST"]],
        "market": [],
    },
    13: {
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
    14: {
        "farmer": ["PLANT", "MELON"],
        "hands": [["WATER"], ["WEST"], ["PASS"], ["WEST"], ["WATER"]],
        "market": [],
    },
    15: {
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
    16: {
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
    17: {
        "farmer": ["PASS"],
        "hands": [["WATER"], ["WEST"], ["PASS"], ["WEST"], ["WATER"]],
        "market": [],
    },
    18: {
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
    19: {
        "farmer": ["PASS"],
        "hands": [["PASS"], ["WATER"], ["PASS"], ["WATER"], ["PLANT", "WHEAT"]],
        "market": [],
    },
    20: {
        "farmer": ["PASS"],
        "hands": [["PASS"], ["PASS"], ["PASS"], ["WEST"], ["WATER"]],
        "market": [],
    },
    21: {
        "farmer": ["PASS"],
        "hands": [["PASS"], ["PASS"], ["PASS"], ["PLANT", "MELON"], ["PASS"]],
        "market": [],
    },
    22: {
        "farmer": ["PASS"],
        "hands": [["PASS"], ["PASS"], ["PASS"], ["WATER"], ["PASS"]],
        "market": [],
    },
    23: {
        "farmer": ["PASS"],
        "hands": [["PASS"], ["PASS"], ["PASS"], ["PASS"], ["PASS"]],
        "market": [],
    },
    24: {
        "farmer": ["PASS"],
        "hands": [["PASS"], ["PASS"], ["PASS"], ["PASS"], ["PASS"]],
        "market": [],
    },
    25: {
        "farmer": ["CARE"],
        "hands": [],
        "market": [["BUY_PRODUCT", "WHEAT", 3]],
    },
    26: {
        "farmer": ["PICKUP", "WHEAT", 3],
        "hands": [],
        "market": [["BUY_PRODUCT", "WHEAT", 2]],
    },
    27: {
        "farmer": ["FEED"],
        "hands": [],
        "market": [["BUY_PRODUCT", "WHEAT", 2]],
    },
    28: {
        "farmer": ["WEST"],
        "hands": [],
        "market": [["BUY_PRODUCT", "WHEAT", 2]],
    },
    29: {
        "farmer": ["FEED"],
        "hands": [],
        "market": [["BUY_PRODUCT", "WHEAT", 2]],
    },
    30: {
        "farmer": ["CARE"],
        "hands": [],
        "market": [["BUY_PRODUCT", "WHEAT", 2]],
    },
    31: {
        "farmer": ["NORTH"],
        "hands": [],
        "market": [["BUY_PRODUCT", "WHEAT", 2]],
    },
    32: {
        "farmer": ["FEED"],
        "hands": [],
        "market": [["BUY_PRODUCT", "WHEAT", 2]],
    },
    33: {
        "farmer": ["CARE"],
        "hands": [],
        "market": [["BUY_PRODUCT", "WHEAT", 2]],
    },
    34: {
        "farmer": ["EAST"],
        "hands": [],
        "market": [["BUY_PRODUCT", "WHEAT", 2]],
    },
    35: {
        "farmer": ["CARE"],
        "hands": [],
        "market": [["BUY_PRODUCT", "WHEAT", 2]],
    },
    36: {
        "farmer": ["COLLECT_FERTILIZER"],
        "hands": [],
        "market": [["BUY_PRODUCT", "WHEAT", 2]],
    },
    37: {
        "farmer": ["SOUTH"],
        "hands": [],
        "market": [["BUY_PRODUCT", "WHEAT", 2]],
    },
    38: {
        "farmer": ["COLLECT_FERTILIZER"],
        "hands": [],
        "market": [["BUY_PRODUCT", "WHEAT", 2]],
    },
    39: {
        "farmer": ["DROP"],
        "hands": [],
        "market": [["BUY_PRODUCT", "WHEAT", 2]],
    },
    40: {
        "farmer": ["WEST"],
        "hands": [],
        "market": [["SELL", "FERTILIZER", 2], ["BUY_PRODUCT", "WHEAT", 2]],
    },
    41: {
        "farmer": ["EAST"],
        "hands": [],
        "market": [["BUY_PRODUCT", "WHEAT", 3]],
    },
    42: {
        "farmer": ["PICKUP", "WHEAT", 1],
        "hands": [],
        "market": [["BUY_PRODUCT", "WHEAT", 3]],
    },
    43: {
        "farmer": ["NORTH"],
        "hands": [],
        "market": [["BUY_PRODUCT", "WHEAT", 2]],
    },
    44: {
        "farmer": ["FEED"],
        "hands": [],
        "market": [["BUY_PRODUCT", "WHEAT", 2]],
    },
    45: {"farmer": ["WEST"], "hands": [], "market": []},
    46: {"farmer": ["COLLECT_FERTILIZER"], "hands": [], "market": []},
    47: {"farmer": ["SOUTH"], "hands": [], "market": []},
    48: {"farmer": ["COLLECT_FERTILIZER"], "hands": [], "market": []},
}
