# Reference: Environment API

This document details the public API and data models for environment wrappers and action builders in `src/environment/`.

---

## Module: `environment.state`

### `class GameState`
Typed dataclass representing a parsed snapshot of the game turn.

```python
@dataclass(slots=True)
class GameState:
    raw: dict
    step: int
    day: int
    hour: int
    player: int
    farm: dict
    private: dict
    market: dict
    money: int
    prices: dict[str, int]
    shed: dict[str, int]
    seeds: dict[str, int]
    tiles: list[list[Any]]
    farmer: tuple[int, int]
    hands: list
    hires_today: int
    unlocked_quadrants: list[str]
    board_size: int
```

#### Factory Methods
* **`classmethod from_obs(obs: dict) -> GameState`**: Factory that safely parses raw observation dictionary from Kaggle engine.

#### Properties & Helper Methods
* `x -> int`: Farmer X coordinate.
* `y -> int`: Farmer Y coordinate.
* `current_tile -> Any`: Data stored in `tiles[y][x]`.
* `price(item: str) -> int`: Current market sale price.
* `inventory(item: str) -> int`: Count of `item` stored in shed.
* `seed_count(crop: str) -> int`: Seed count in seed storage.
* `has_seed(crop: str) -> bool`: Returns `True` if `seed_count(crop) > 0`.
* `can_afford(amount: int) -> bool`: Returns `True` if `self.money >= amount`.

---

### Raw Observation Schema

The raw observation dictionary provided to `agent(obs)` by the Kaggle engine:

```python
{
    "player": int,           # 0 or 1
    "step":   int,           # 0-indexed overall turn (0..719)
    "day":    int,           # 0-indexed day (0..29)
    "hour":   int,           # 0-indexed hour (0..23)
    "farms": [
        {
            "money":              float,
            "tiles":              list[list[Any]],  # tiles[y][x] 10x10 grid
            "farmer":             [int, int],       # [x, y] coordinates
            "hands":              list[list[int]],  # [[x, y], ...] for active hired hands
            "unlocked_quadrants": list[str],        # Subset of ["NW", "NE", "SW", "SE"]
            "hires_today":        int,              # Hires made today (determines next HIRE cost)
        },
        ... # Player 1 farm
    ],
    "market": {
        "inventory": dict[str, int],  # Current market item supply
        "prices":    dict[str, int],  # Current dynamic selling price
    },
    "town": {
        "unlocked_shops": list[str],  # Active shop names (e.g. ["BAKERY", "PET_CAFE"])
    },
    "private": {
        "shed":        dict[str, int],  # Storage inventory (non-seeds, max 100)
        "seeds":       dict[str, int],  # Seed storage (uncapped)
        "inventories": list[dict[str, int]], # [main_farmer_inv, hand1_inv, ...]
    }
}
```

#### Tile Data Structures

Each cell in `farm["tiles"][y][x]` contains one of:

1. **`None`**: Empty unlocked tile.
2. **`"LOCKED"`**: Unbought quadrant tile (passable by units, but tile operations are no-ops).
3. **Plant Dict**:
   ```python
   {
       "kind":                 "PLANT",
       "crop":                 str,   # "WHEAT" | "CARROT" | "TOMATO" | "STRAWBERRY" | "MELON"
       "planted_day":          int,
       "watered_today":        bool,  # Resets to False at end-of-day
       "consecutive_unwatered":int,   # >=2 converts tile to WEED
       "yield_units":          int,   # Unharvested units on tile
       "max_lifespan_step":    int,   # Step when decay begins (-1 for ongoing crops)
       "fertilized_until_day": int,   # Last day fertilizer applies (-1 if none)
   }
   ```
4. **Weed Dict**: `{"kind": "WEED"}`
5. **Animal Structure Dict**:
   ```python
   {
       "kind":                 str,   # "COOP" | "PASTURE"
       "animal":               str | None, # "GOOSE" | "COW" | "SHEEP" | None
       "placed_day":           int,
       "yield_units":          int,
       "fed_today":            bool,
       "consecutive_unfed":    int,   # >=2 causes animal escape
       "cared_today":          bool,
       "fertilizer_available": bool,  # 1 available at end-of-day; cleared by COLLECT_FERTILIZER
       "pending_care_bonus":   int,   # Banked bonus for next scheduled yield
   }
   ```

---

## Module: `environment.board`

### `class Tile`
Encapsulates a grid coordinate and its state object.

```python
@dataclass(slots=True)
class Tile:
    x: int
    y: int
    data: Any
```

* `empty -> bool`: `True` if `data is None`.
* `is_plant -> bool`: `True` if `data` is a plant dictionary (`kind == "PLANT"`).
* `crop -> str | None`: Crop name (`WHEAT`, `CARROT`, `TOMATO`, `STRAWBERRY`, `MELON`) or `None`.
* `watered -> bool`: `True` if watered today.
* `yield_units -> int`: Current unharvested yield units on tile.
* `planted_day -> int | None`: In-game day planted.
* `distance(x: int, y: int) -> int`: Manhattan distance `|self.x - x| + |self.y - y|`.

---

### `class Board`
Spatial query generator over the farm grid.

```python
class Board:
    def __init__(self, state: GameState) -> None: ...
```

* `all_tiles() -> Generator[Tile]`: Yields all tiles across `board_size * board_size`.
* `empty_tiles() -> Generator[Tile]`: Yields empty unlocked tiles (`data is None`).
* `plants() -> Generator[Tile]`: Yields all plant tiles.
* `crops(crop: str) -> Generator[Tile]`: Yields plants matching specific crop string.
* `harvestable() -> Generator[Tile]`: Yields plants with `yield_units > 0`.
* `needs_water() -> Generator[Tile]`: Yields unwatered plants (`watered_today == False`).
* `nearest(tiles: Iterable[Tile]) -> Tile | None`: Returns tile from iterator minimizing Manhattan distance to farmer.

---

## Module: `environment.economy`

### `class Economy`
Financial evaluator for seed costs, market prices, and return on investment (ROI).

```python
class Economy:
    def __init__(self, state: GameState) -> None: ...
```

* `price(item: str) -> int`: Current price in market.
* `inventory(item: str) -> int`: Item count in player shed.
* `seeds(crop: str) -> int`: Seed count in player storage.
* `crop_cost(crop: str) -> int`: Cost of single seed from `CROPS` configuration.
* `crop_grow_days(crop: str) -> int`: Max yield growth duration in days.
* `crop_revenue(crop: str) -> int`: Current market value per harvested unit.
* `crop_profit(crop: str) -> float`: `revenue - seed_cost`.
* `crop_roi(crop: str) -> float`: `profit / max(1, grow_days)`.
* `best_crop() -> str | None`: Returns crop string with highest current ROI.
* `should_sell(item: str) -> bool`: Returns `True` if inventory > 0 and price > cost.
* `should_buy_seed(crop: str) -> bool`: Returns `True` if holding 0 seeds and balance >= cost.
* `should_expand() -> bool`: Returns `True` if `money > 5000`.
* `should_hire() -> bool`: Returns `True` if `money > 10000`.

---

## Module: `environment.market`

### `class Market`
Statistical price tracker and trend detector across turns.

```python
class Market:
    HISTORY_LEN = 20
    def __init__(self, state: GameState) -> None: ...
```

* `average(item: str) -> float`: Rolling mean price over last 20 turns.
* `minimum(item: str) -> int`: Rolling minimum price.
* `maximum(item: str) -> int`: Rolling maximum price.
* `trend(item: str) -> int`: Price change `history[-1] - history[0]`.
* `normalized_price(item: str) -> float`: Price percentile `(now - min) / (max - min)` in `[0.0, 1.0]`.
* `expensive(item: str) -> bool`: Returns `True` if `normalized_price >= 0.80`.
* `cheap(item: str) -> bool`: Returns `True` if `normalized_price <= 0.20`.
* `sell_score(item: str) -> float`: Composite score combining price, trend, and percentile.
* `best_item_to_sell() -> str | None`: Identifies shed item with highest sell score.

---

## Module: `environment.actions`

### `class Action`
Container for a single turn's submitted actions.

```python
@dataclass(slots=True)
class Action:
    score: float = 0.0
    farmer: list = field(default_factory=lambda: ["PASS"])
    hands: list = field(default_factory=list)
    market: list = field(default_factory=list)

    def to_dict(self) -> dict: ...
```

---

### `class ActionBuilder`
Static factory for constructing standard game action structures.

| Factory Method | Generated Operation Payload | Notes |
| :--- | :--- | :--- |
| `pass_turn()` | `farmer: ["PASS"]` | Idle operation. |
| `move(direction)` | `farmer: [direction]` | `"NORTH"`, `"SOUTH"`, `"EAST"`, `"WEST"`. |
| `plant(crop)` | `farmer: ["PLANT", crop]` | Consumes seed directly from seed bank. |
| `water()` | `farmer: ["WATER"]` | Waters crop underfoot. |
| `harvest()` | `farmer: ["HARVEST"]` | Adds produce to carried inventory. |
| `fertilize()` | `farmer: ["FERTILIZE"]` | Doubles watering bonus for 3 days. |
| `dig()` | `farmer: ["DIG"]` | Clears weed or empty coop/pasture. |
| `pickup(item, n)` | `farmer: ["PICKUP", item, n]` | From adjacent shed. |
| `place(item, n)` | `farmer: ["PLACE", item, n]` | Place animal on structure or drop into shed. |
| `drop()` | `farmer: ["DROP"]` | Dumps inventory into adjacent shed. |
| `build_coop()` | `farmer: ["BUILD_COOP"]` | Builds coop for geese. |
| `build_pasture()` | `farmer: ["BUILD_PASTURE"]` | Builds pasture for cows/sheep. |
| `feed()` | `farmer: ["FEED"]` | Consumes 1 wheat to feed animal. |
| `care()` | `farmer: ["CARE"]` | Banks care bonus for next yield. |
| `collect_fertilizer()`| `farmer: ["COLLECT_FERTILIZER"]` | Gathers 1 fertilizer. |
| `buy_seed(crop, n)` | `market: [["BUY_SEED", crop, n]]` | Market order. |
| `buy_product(item, n)`| `market: [["BUY_PRODUCT", item, n]]` | Buy back wheat or fertilizer. |
| `buy_animal(animal, n)`| `market: [["BUY_ANIMAL", animal, n]]` | Market animal order. |
| `sell(item, n)` | `market: [["SELL", item, n]]` | Sell harvested goods. |
| `buy_land()` | `market: [["BUY_LAND"]]` | Unlocks next quadrant. |
| `hire_hand()` | `market: [["HIRE"]]` | Hires additional worker for day. |
| `merge(*actions)` | `Action` | Merges non-conflicting unit and market orders. |
