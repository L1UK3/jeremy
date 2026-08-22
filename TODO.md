# Jeremy Kaggriculture — Project Status & Roadmap (TODO)

This document tracks the implementation and integration status of all modules, classes, and mechanics across the **Jeremy** codebase, along with prioritized architectural and feature tasks.

---

## 1. Overall Module Integration Summary

| Module | Implementation | Decision Loop Integration | Responsibility & Notes |
| :--- | :---: | :---: | :--- |
| [`src/environment/state.py`](src/environment/state.py) | <font color="green">**100%**</font> | <font color="green">**100% (Full)**</font> | Observation wrapper, coordinate getters (`x`, `y`), price & inventory queries |
| [`src/environment/board.py`](src/environment/board.py) | <font color="green">**100%**</font> | <font color="green">**85% (High)**</font> | Spatial grid, tile generators (`empty_tiles`, `harvestable`, `needs_water`), Manhattan distance search |
| [`src/environment/economy.py`](src/environment/economy.py) | <font color="green">**100%**</font> | <font color="green">**75% (High)**</font> | ROI calculations, crop selection, `should_sell`, `should_buy_seed`, `should_expand` |
| [`src/agent/search.py`](src/agent/search.py) | <font color="green">**100%**</font> | <font color="green">**100% (Full)**</font> | Scored candidate action pool, top-$k$ sorting, decision selection |
| [`src/environment/actions.py`](src/environment/actions.py) | <font color="green">**100%**</font> | <font color="orange">**45% (Partial)**</font> | Action factory (`move`, `harvest`, `water`, `plant`, `sell`, `buy_seed`, `buy_land`, `merge` used) |
| [`src/environment/market.py`](src/environment/market.py) | <font color="green">**100%**</font> | <font color="red">**0% (Unused)**</font> | 20-turn price history, trend calculation, normalization, `sell_score` |
| [`src/agent/scheduler.py`](src/agent/scheduler.py) | <font color="green">**100%**</font> | <font color="red">**0% (Unused)**</font> | Multi-unit spatial task dispatching for farmer + hired farmhands |

---

## 2. Detailed Module Breakdown & Integration

### State (`src/environment/state.py`)
- **Status**: <font color="green">Fully Integrated (100%)</font>
- **Purpose**: Typed dataclass wrapping raw Kaggle observation dicts.

| Feature / Method | Implemented | In Planner | Notes / Action Item |
| :--- | :---: | :---: | :--- |
| `GameState.from_obs(obs)` | <font color="green">Yes</font> | <font color="green">Yes</font> | Parses raw observation into structured state |
| `x`, `y` | <font color="green">Yes</font> | <font color="green">Yes</font> | Properties alias `farmer[0]`, `farmer[1]` |
| `current_tile` | <font color="green">Yes</font> | <font color="green">Yes</font> | Returns tile under farmer (`tiles[y][x]`) |
| `price(item)`, `inventory(item)` | <font color="green">Yes</font> | <font color="green">Yes</font> | Fetches market prices and shed stock |
| `seed_count(crop)`, `has_seed(crop)` | <font color="green">Yes</font> | <font color="green">Yes</font> | Fast checks on seed storage |
| `can_afford(amount)` | <font color="green">Yes</font> | <font color="green">Yes</font> | Checks `money >= amount` |

---

### Board (`src/environment/board.py`)
- **Status**: <font color="green">Mostly Integrated (~85%)</font>
- **Purpose**: Tile wrappers, generators, and Manhattan distance pathfinding.

| Feature / Method | Implemented | In Planner | Notes / Action Item |
| :--- | :---: | :---: | :--- |
| `Tile` properties (`empty`, `is_plant`, `crop`, `watered`, `yield_units`, `planted_day`) | <font color="green">Yes</font> | <font color="green">Yes</font> | Encapsulates single tile attributes |
| `Tile.distance(x, y)` | <font color="green">Yes</font> | <font color="green">Yes</font> | Manhattan distance calculation |
| `all_tiles()`, `empty_tiles()`, `plants()` | <font color="green">Yes</font> | <font color="green">Yes</font> | Grid generators |
| `harvestable()`, `needs_water()` | <font color="green">Yes</font> | <font color="green">Yes</font> | Target generators for immediate farm tasks |
| `nearest(tiles)` | <font color="green">Yes</font> | <font color="green">Yes</font> | Finds closest matching tile to the farmer |
| `crops(crop)` | <font color="green">Yes</font> | <font color="red">No</font> | Filter tiles by specific crop type |

---

### Economy (`src/environment/economy.py`)
- **Status**: <font color="green">Mostly Integrated (~75%)</font>
- **Purpose**: Financial calculations, profit per day (ROI), crop selection, affordability.

| Feature / Method | Implemented | In Planner | Notes / Action Item |
| :--- | :---: | :---: | :--- |
| `price(item)`, `inventory(item)`, `seeds(crop)` | <font color="green">Yes</font> | <font color="green">Yes</font> | Query state properties |
| `crop_cost(crop)`, `crop_grow_days(crop)` | <font color="green">Yes</font> | <font color="green">Yes</font> | Lookups from `CROPS` table |
| `crop_revenue(crop)`, `crop_profit(crop)` | <font color="green">Yes</font> | <font color="green">Yes</font> | Calculates revenue and net profit per crop |
| `crop_roi(crop)` | <font color="green">Yes</font> | <font color="green">Yes</font> | Profit per grow day for crop prioritization |
| `best_crop()` | <font color="green">Yes</font> | <font color="green">Yes</font> | Finds highest ROI crop |
| `should_sell(item)` | <font color="green">Yes</font> | <font color="green">Yes</font> | Checks `inventory > 0` and `price > cost` |
| `should_buy_seed(crop)` | <font color="green">Yes</font> | <font color="green">Yes</font> | Checks `seeds == 0` and affordability |
| `should_expand()` | <font color="green">Yes</font> | <font color="green">Yes</font> | Trigger to buy land when `money > 5000` |
| `should_hire()` | <font color="green">Yes</font> | <font color="red">No</font> | Trigger to hire extra farmhands when `money > 10000` |

---

### Actions (`src/environment/actions.py`)
- **Status**: <font color="orange">Partially Integrated (~45%)</font>
- **Purpose**: Standardized action builders for all game interactions.

| Category | Method | Implemented | In Planner | Action Item / Target Utility |
| :--- | :--- | :---: | :---: | :--- |
| **Movement & Core** | `pass_turn()` | <font color="green">Yes</font> | <font color="green">Yes</font> | Idle fallback |
| | `move(direction)` | <font color="green">Yes</font> | <font color="green">Yes</font> | Directional movement (`score = 20-40`) |
| | `merge(*actions)` | <font color="green">Yes</font> | <font color="green">Yes</font> | Combines 1 farmer action + market orders |
| **Farming** | `harvest()` | <font color="green">Yes</font> | <font color="green">Yes</font> | Harvest mature crop (`score = 100 + value`) |
| | `water()` | <font color="green">Yes</font> | <font color="green">Yes</font> | Water unwatered plant (`score = 80`) |
| | `plant(crop)` | <font color="green">Yes</font> | <font color="green">Yes</font> | Plant highest-ROI seed (`score = 60 + roi`) |
| | `dig()` | <font color="green">Yes</font> | <font color="red">No</font> | **TODO**: Clear weeds on current tile (`score = 90`) |
| | `fertilize()` | <font color="green">Yes</font> | <font color="red">No</font> | **TODO**: Apply fertilizer for yield bonus |
| **Market Orders** | `sell(item, amount)` | <font color="green">Yes</font> | <font color="green">Yes</font> | Sell produce (`score = 50`) |
| | `buy_seed(crop, amount)` | <font color="green">Yes</font> | <font color="green">Yes</font> | Buy seeds (`score = 40`) |
| | `buy_land(x, y)` | <font color="green">Yes</font> | <font color="green">Yes</font> | Buy quadrant (`score = 100`) |
| | `hire_hand()` | <font color="green">Yes</font> | <font color="red">No</font> | **TODO**: Hire worker when affordable |
| | `buy_product(item, amount)` | <font color="green">Yes</font> | <font color="red">No</font> | **TODO**: Buy wheat / fertilizer |
| | `buy_animal(animal, amount)` | <font color="green">Yes</font> | <font color="red">No</font> | **TODO**: Buy Goose / Cow / Sheep |
| **Animals & Coops** | `build_coop()` | <font color="green">Yes</font> | <font color="red">No</font> | **TODO**: Construct coop structure |
| | `build_pasture()` | <font color="green">Yes</font> | <font color="red">No</font> | **TODO**: Construct pasture structure |
| | `feed()` | <font color="green">Yes</font> | <font color="red">No</font> | **TODO**: Feed animal with wheat |
| | `care()` | <font color="green">Yes</font> | <font color="red">No</font> | **TODO**: Pet / care for animal |
| | `collect_fertilizer()` | <font color="green">Yes</font> | <font color="red">No</font> | **TODO**: Collect animal byproduct |
| **Shed Transfer** | `pickup(item, amount)` | <font color="green">Yes</font> | <font color="red">No</font> | **TODO**: Withdraw items from shed |
| | `place(item, amount)` | <font color="green">Yes</font> | <font color="red">No</font> | **TODO**: Place animal or inventory |
| | `drop()` | <font color="green">Yes</font> | <font color="red">No</font> | **TODO**: Dump carried items into shed |

---

### Market Intelligence (`src/environment/market.py`)
- **Status**: <font color="red">Unused in Planner (0%)</font>
- **Purpose**: Price history tracking, normalization, rolling average/trend, and composite sell score.

| Feature / Method | Implemented | In Planner | Action Item |
| :--- | :---: | :---: | :--- |
| `Market._history`, `_update()` | <font color="green">Yes</font> | <font color="red">No</font> | Stores last 20 turns of prices per good |
| `average(item)`, `minimum(item)`, `maximum(item)` | <font color="green">Yes</font> | <font color="red">No</font> | Historical price statistical bounds |
| `trend(item)` | <font color="green">Yes</font> | <font color="red">No</font> | Price trajectory slope over window |
| `normalized_price(item)` | <font color="green">Yes</font> | <font color="red">No</font> | Relative price index between min and max |
| `expensive(item)`, `cheap(item)` | <font color="green">Yes</font> | <font color="red">No</font> | Sell at peaks ($\ge 0.80$) / buy at dips ($\le 0.20$) |
| `sell_score(item)` | <font color="green">Yes</font> | <font color="red">No</font> | Composite ranking for shed inventory sales |
| `best_item_to_sell()` | <font color="green">Yes</font> | <font color="red">No</font> | Ranks all shed goods to pick optimal sale |

---

### Multi-Unit Scheduler (`src/agent/scheduler.py`)
- **Status**: <font color="red">Unused in Planner (0%)</font>
- **Purpose**: Spatial task allocation preventing conflicting unit movements/actions.

| Feature / Method | Implemented | In Planner | Action Item |
| :--- | :---: | :---: | :--- |
| `Job` dataclass | <font color="green">Yes</font> | <font color="red">No</font> | Priority, action, target coordinates, actor |
| `add_job(...)`, `sort()`, `best()` | <font color="green">Yes</font> | <font color="red">No</font> | Priority job queue |
| `assign()` | <font color="green">Yes</font> | <font color="red">No</font> | Greedily assigns jobs to farmer and farmhands without coordinate collision |
| `clear()` | <font color="green">Yes</font> | <font color="red">No</font> | Reset job pool between turns |

---
