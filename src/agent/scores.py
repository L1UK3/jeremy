"""Score constants for heuristic evaluation of actions and task utilities."""

# Top Physical Priorities
HARVEST_BASE: float = 150.0
WATER: float = 120.0

# Top Market Orders
BUY_SEED: float = 100.0
HIRE_HAND: float = 95.0
SELL: float = 90.0

# Farm Expansion & Seeding
BUY_LAND: float = 85.0
PLANT_BASE: float = 75.0
DIG_WEED: float = 60.0
FERTILIZER: float = 50.0

# Single-unit Movement
MOVE_HARVEST: float = 40.0
MOVE_WATER: float = 35.0
MOVE_WEED: float = 30.0
MOVE_EMPTY: float = 20.0

__all__ = [
    "BUY_LAND",
    "BUY_SEED",
    "DIG_WEED",
    "FERTILIZER",
    "HARVEST_BASE",
    "HIRE_HAND",
    "MOVE_EMPTY",
    "MOVE_HARVEST",
    "MOVE_WATER",
    "MOVE_WEED",
    "PLANT_BASE",
    "SELL",
    "WATER",
]

