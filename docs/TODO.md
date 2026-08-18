# Environment Integration Status

This document tracks the integration status of all classes, methods, and mechanics from [`src/environment`](../src/environment) and [`src/agent`](../src/agent) into the main rule-based agent decision loop.

---

## Overall Integration Summary

| Module | Integration Level | Primary Responsibility |
| :--- | :--- | :--- |
| [`src/environment/market.py`](../src/environment/market.py) | <font color="red">**0% (Unused)**</font> | Price trend tracking, historical statistics, optimal sell timing |
| [`src/environment/economy.py`](../src/environment/economy.py) | <font color="orange">**~60% (Partial)**</font> | ROI calculations, best crops, expansion & hire rules |
| [`src/environment/actions.py`](../src/environment/actions.py) | <font color="orange">**~40% (Partial)**</font> | Action construction for crops, animals, land, farmhands, shed |
| [`src/environment/board.py`](../src/environment/board.py) | <font color="green">**~80% (Mostly Integrated)**</font> | Spatial map representation, tile querying, and distance search |
| [`src/environment/state.py`](../src/environment/state.py) | <font color="green">**~90% (Fully Integrated)**</font> | Observation wrapper and state convenience getters |
| [`src/agent/scheduler.py`](../src/agent/scheduler.py) | <font color="red">**0% (Unused)**</font> | Multi-unit task scheduling for farmer and hired farmhands |
| [`src/agent/search.py`](../src/agent/search.py) | <font color="green">**100% (Integrated)**</font> | Candidate scoring, decision selection, and top-K ranking |

---

## Detailed Module Breakdown

### Market (`src/environment/market.py`)
- **Status**: <font color="red">Unused (0%)</font>
- **Purpose**: Price history tracking, normalization, and sell score calculation.

| Feature / Method | Status | Notes / Action Item |
| :--- | :---: | :--- |
| `Market._history`, `_update()` | <font color="red">No</font> | Tracks last 20 turns of prices |
| `average(item)`, `minimum(item)`, `maximum(item)` | <font color="red">No</font> | Price ranges over time |
| `trend(item)` | <font color="red">No</font> | Price slope/direction over recent window |
| `normalized_price(item)` | <font color="red">No</font> | Relative price index between min and max |
| `expensive(item)`, `cheap(item)` | <font color="red">No</font> | Threshold checks for price peaks (>= 80%) / floors (<= 20%) |
| `sell_score(item)` | <font color="red">No</font> | Composite score combining current price, trend, and normalization |
| `best_item_to_sell()` | <font color="red">No</font> | Ranks shed items to select the highest-profit good to sell |

---

### Economy (`src/environment/economy.py`)
- **Status**: <font color="orange">Partially Integrated (~60%)</font>
- **Purpose**: Financial calculations, profit per day (ROI), crop selection, and affordability checks.

| Feature / Method | Status | Notes / Action Item |
| :--- | :---: | :--- |
| `price(item)` | <font color="green">Yes</font> | Fetch current market price |
| `inventory(item)` | <font color="green">Yes</font> | Fetch shed inventory count |
| `seeds(crop)` | <font color="green">Yes</font> | Fetch seed count in storage |
| `crop_cost(crop)`, `crop_grow_days(crop)` | <font color="green">Yes</font> | Seed purchase cost and growth duration |
| `crop_revenue(crop)`, `crop_profit(crop)` | <font color="green">Yes</font> | Revenue and net profit per crop cycle |
| `crop_roi(crop)` | <font color="green">Yes</font> | Profit per grow day for crop prioritization |
| `best_crop()` | <font color="green">Yes</font> | Finds highest ROI crop |
| `should_sell(item)` | <font color="green">Yes</font> | Basic check: inventory > 0 and price > seed cost |
| `should_buy_seed(crop)` | <font color="green">Yes</font> | Checks if seeds needed and affordable |
| `should_expand()` | <font color="red">No</font> | Trigger to buy additional land quadrant when `money > 5000` |
| `should_hire()` | <font color="red">No</font> | Trigger to hire extra farmhands when `money > 10000` |

---

### Actions (`src/environment/actions.py`)
- **Status**: <font color="orange">Partially Integrated (~40%)</font>
- **Purpose**: Standardized action builders for all game interactions.

| Action Category | Method | Status | Description |
| :--- | :--- | :---: | :--- |
| **Turn & Movement** | `pass_turn()` | <font color="green">Yes</font> | Do nothing for current turn |
| | `move(direction)` | <font color="green">Yes</font> | Move farmer `NORTH`, `SOUTH`, `EAST`, `WEST` |
| | `merge(*actions)` | <font color="green">Yes</font> | Merge multi-component actions (farmer + market + hands) |
| **Crops** | `plant(crop)` | <font color="green">Yes</font> | Plant seed on empty tile |
| | `water()` | <font color="green">Yes</font> | Water plant on current tile |
| | `harvest()` | <font color="green">Yes</font> | Harvest mature crop on current tile |
| | `fertilize()` | <font color="red">No</font> | Double watering bonus / boost ongoing crop yield |
| | `dig()` | <font color="red">No</font> | Remove weeds or clear dead plants |
| **Market Orders** | `buy_seed(crop, amount)` | <font color="green">Yes</font> | Purchase seeds from market |
| | `sell(item, amount)` | <font color="green">Yes</font> | Sell produce to market |
| | `buy_product(item, amount)` | <font color="red">No</font> | Buy back wheat or fertilizer from market |
| | `buy_animal(animal, amount)` | <font color="red">No</font> | Buy Goose, Cow, or Sheep |
| | `buy_land()` | <font color="red">No</font> | Unlock NE, SW, or SE quadrant |
| | `hire_hand()` | <font color="red">No</font> | Hire an extra farmhand for the day |
| **Animals & Coops** | `build_coop()` | <font color="red">No</font> | Construct coop for Goose (eggs) |
| | `build_pasture()` | <font color="red">No</font> | Construct pasture for Cow (milk) / Sheep (wool) |
| | `feed()` | <font color="red">No</font> | Feed wheat to animal on current structure |
| | `care()` | <font color="red">No</font> | Bank care bonus for next payout |
| | `collect_fertilizer()` | <font color="red">No</font> | Gather fertilizer from animal |
| **Shed Transfer** | `pickup(item, amount)` | <font color="red">No</font> | Withdraw items from shed |
| | `place(item, amount)` | <font color="red">No</font> | Place animal on structure or drop items into shed |
| | `drop()` | <font color="red">No</font> | Dump carried inventory into shed when adjacent |

---

### Board (`src/environment/board.py`)
- **Status**: <font color="green">Mostly Integrated (~80%)</font>
- **Purpose**: Grid queries, tile state wrappers, and path distance search.

| Feature / Method | Status | Notes / Action Item |
| :--- | :---: | :--- |
| `Tile` properties (`empty`, `is_plant`, `crop`, `watered`, `yield_units`, `planted_day`) | <font color="green">Yes</font> | Encapsulates single tile attributes |
| `Tile.distance(x, y)` | <font color="green">Yes</font> | Manhattan distance calculation |
| `all_tiles()`, `empty_tiles()`, `plants()` | <font color="green">Yes</font> | Grid generators |
| `harvestable()`, `needs_water()` | <font color="green">Yes</font> | Target generators for immediate farm tasks |
| `nearest(tiles)` | <font color="green">Yes</font> | Finds closest matching tile to the farmer |
| `crops(crop)` | <font color="red">No</font> | Filter tiles by specific crop type |

---

### GameState (`src/environment/state.py`)
- **Status**: <font color="green">Fully Integrated (~90%)</font>
- **Purpose**: Typed wrapper around raw observation dictionary.

| Feature / Method | Status | Notes / Action Item |
| :--- | :---: | :--- |
| `GameState.from_obs(obs)` | <font color="green">Yes</font> | Parses Kaggle observation into structured object |
| `current_tile` | <font color="green">Yes</font> | Returns data for tile under main farmer |
| `price(item)`, `inventory(item)` | <font color="green">Yes</font> | Quick access to market prices and shed stock |
| `seed_count(crop)`, `has_seed(crop)` | <font color="green">Yes</font> | Quick access to seed inventory |
| `can_afford(amount)` | <font color="green">Yes</font> | Checks if bank balance >= cost |
| `x`, `y` | <font color="red">No</font> | Direct aliases for farmer coordinates (`farmer[0]`, `farmer[1]`) |

---

### Scheduler (`src/agent/scheduler.py`)
- **Status**: <font color="red">Unused (0%)</font>
- **Purpose**: Multi-agent task assignment when farmhands are hired.

| Feature / Method | Status | Notes / Action Item |
| :--- | :---: | :--- |
| `Job` dataclass | <font color="red">No</font> | Defines priority, target coordinates, action, and assigned worker |
| `add_job(...)`, `sort()`, `best()` | <font color="red">No</font> | Priority job queue |
| `assign()` | <font color="red">No</font> | Dispatches highest priority jobs to farmer and hired hands without overlap |

---

