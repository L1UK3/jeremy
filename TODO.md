# Jeremy Kaggriculture — Project Status & Roadmap (TODO)

This document tracks the implementation, integration status, and development roadmap for all modules, classes, and mechanics across the **Jeremy** codebase.

---

## Overall Module Integration in Planner

| Module / Subsystem                                         |           Implementation            |              Planner Integration               | Status & Responsibility                                                                                                                        |
| :--------------------------------------------------------- | :---------------------------------: | :--------------------------------------------: | :--------------------------------------------------------------------------------------------------------------------------------------------- |
| [`src/main.py`](src/main.py)                               | <font color="green">**100%**</font> |   <font color="green">**100% (Full)**</font>   | Kaggle entrypoint: exports `agent(obs)`, executes `Planner(state).play().to_dict()`                                                            |
| [`src/environment/state.py`](src/environment/state.py)     | <font color="green">**100%**</font> |   <font color="green">**100% (Full)**</font>   | Typed observation wrapper dataclass, coordinates (`x`, `y`), price & inventory queries, financial affordability                                |
| [`src/environment/board.py`](src/environment/board.py)     | <font color="green">**100%**</font> |   <font color="green">**90% (High)**</font>    | Spatial grid, tile model (`Tile`), generators (`empty_tiles`, `plants`, `weeds`, `harvestable`, `needs_water`), `nearest()`, `nearest_other()` |
| [`src/environment/economy.py`](src/environment/economy.py) | <font color="green">**100%**</font> |   <font color="green">**75% (High)**</font>    | ROI calculations, crop selection (`best_crop`), `should_sell`, `should_buy_seed`, `should_expand`, `should_hire`                               |
| [`src/environment/actions.py`](src/environment/actions.py) | <font color="green">**100%**</font> | <font color="orange">**45% (Moderate)**</font> | Action factory (`move`, `harvest`, `water`, `plant`, `dig`, `sell`, `buy_seed`, `buy_land`, `merge` actively used)                             |
| [`src/agent/config.py`](src/agent/config.py)               | <font color="green">**100%**</font> |   <font color="green">**100% (Full)**</font>   | Strategy configuration dataclass (`target_crop`, `sell_threshold`, `seed_target`, `expand_land`, `max_hires_per_day`)                          |
| [`src/agent/search.py`](src/agent/search.py)               | <font color="green">**100%**</font> |   <font color="green">**100% (Full)**</font>   | Scored candidate action pool (`Node`), top-$k$ sorting, decision selection                                                                     |
| [`src/agent/planner.py`](src/agent/planner.py)             | <font color="green">**100%**</font> |   <font color="green">**100% (Full)**</font>   | Turn decision coordinator (evaluates market, current tile, planting, movement, expansion)                                                      |
| [`src/environment/market.py`](src/environment/market.py)   | <font color="green">**100%**</font> |    <font color="red">**0% (Unused)**</font>    | Rolling 20-turn price history, trend indicators, normalized prices, `sell_score`, `best_item_to_sell`                                          |
| [`src/agent/scheduler.py`](src/agent/scheduler.py)         | <font color="green">**100%**</font> |    <font color="red">**0% (Unused)**</font>    | Multi-unit spatial task dispatching for farmer + hired farmhands (`Job`, `add_job`, `assign`)                                                  |
| [`tests/`](tests/) (Test Suite)                            | <font color="orange">**20%**</font> |      <font color="red">**Broken**</font>       | Unit test suite (legacy fixture structure requires overhaul for `GameState`, `Board`, `Economy`, `Market`, `Actions`, `Planner`)               |

---

## Detailed Module Breakdown & Integration

### State (`src/environment/state.py`)

**Status**: <font color="green">Fully Integrated (100%)</font>

| Feature / Method                     |          Implemented           |             In Planner              | Notes / Action Item                                              |
| :----------------------------------- | :----------------------------: | :---------------------------------: | :--------------------------------------------------------------- |
| `GameState.from_obs(obs)`            | <font color="green">Yes</font> |   <font color="green">Yes</font>    | Factory method parsing raw observation dict into `GameState`     |
| `x`, `y`                             | <font color="green">Yes</font> |   <font color="green">Yes</font>    | Property aliases for farmer coordinates `farmer[0]`, `farmer[1]` |
| `current_tile`                       | <font color="green">Yes</font> |   <font color="green">Yes</font>    | Returns raw tile content under the farmer (`tiles[y][x]`)        |
| `price(item)`                        | <font color="green">Yes</font> |   <font color="green">Yes</font>    | Market price lookup (`prices.get(item, 0)`)                      |
| `inventory(item)`                    | <font color="green">Yes</font> |   <font color="green">Yes</font>    | Shed inventory count (`shed.get(item, 0)`)                       |
| `seed_count(crop)`, `has_seed(crop)` | <font color="green">Yes</font> |   <font color="green">Yes</font>    | Seed inventory queries (`seeds.get(crop, 0)`)                    |
| `can_afford(amount)`                 | <font color="green">Yes</font> |   <font color="green">Yes</font>    | Checks `money >= amount`                                         |
| `step`, `day`, `hour`, `player`      | <font color="green">Yes</font> |   <font color="green">Yes</font>    | Core temporal and agent identification fields                    |
| `hands`, `hires_today`               | <font color="green">Yes</font> |     <font color="red">No</font>     | Expose hired farmhand positions and hiring capacity              |
| `unlocked_quadrants`                 | <font color="green">Yes</font> | <font color="orange">Partial</font> | Track unlocked quadrants (`NW`, `NE`, `SW`, `SE`)                |

---

### Board (`src/environment/board.py`)

**Status**: <font color="green">Mostly Integrated (~90%)</font>

| Feature / Method                                                                                           |          Implemented           |           In Planner           | Notes / Action                                                  |
| :--------------------------------------------------------------------------------------------------------- | :----------------------------: | :----------------------------: | :-------------------------------------------------------------- |
| `Tile` properties (`pos`, `empty`, `is_plant`, `is_weed`, `crop`, `watered`, `yield_units`, `planted_day`) | <font color="green">Yes</font> | <font color="green">Yes</font> | Encapsulates single tile attributes and status checks           |
| `Tile.age(current_day)`                                                                                    | <font color="green">Yes</font> | <font color="green">Yes</font> | Calculates days elapsed since planting                          |
| `Tile.is_ripe(current_day)`                                                                                | <font color="green">Yes</font> | <font color="green">Yes</font> | Checks if plant age $\ge$ `max_yield_day` and `yield_units > 0` |
| `Tile.distance(x, y)`                                                                                      | <font color="green">Yes</font> | <font color="green">Yes</font> | Computes Manhattan distance to target coordinates               |
| `all_tiles()`, `empty_tiles()`, `plants()`                                                                 | <font color="green">Yes</font> | <font color="green">Yes</font> | Grid generators for broad spatial iteration                     |
| `crops(crop)`                                                                                              | <font color="green">Yes</font> | <font color="green">Yes</font> | Filter plant tiles by specific crop type                        |
| `harvestable(crop)`, `needs_water(crop)`                                                                   | <font color="green">Yes</font> | <font color="green">Yes</font> | Target generators with optional crop filtering                  |
| `nearest(tiles)`                                                                                           | <font color="green">Yes</font> | <font color="green">Yes</font> | Finds closest matching tile to the farmer                       |
| `nearest_other(tiles)`                                                                                     | <font color="green">Yes</font> | <font color="green">Yes</font> | Finds closest tile excluding the farmer's current coordinates   |
| `weeds()`                                                                                                  | <font color="green">Yes</font> |  <font color="red">No</font>   | Target and navigate toward distant weeds during idle periods    |

---

### Economy (`src/environment/economy.py`)

**Status**: <font color="green">Mostly Integrated (~75%)</font>

| Feature / Method                                |          Implemented           |           In Planner           | Notes / Action                                                             |
| :---------------------------------------------- | :----------------------------: | :----------------------------: | :------------------------------------------------------------------------- |
| `price(item)`, `inventory(item)`, `seeds(crop)` | <font color="green">Yes</font> | <font color="green">Yes</font> | Delegates queries to underlying `GameState`                                |
| `crop_cost(crop)`, `crop_grow_days(crop)`       | <font color="green">Yes</font> | <font color="green">Yes</font> | Metadata lookups from official `CROPS` dictionary                          |
| `crop_revenue(crop)`, `crop_profit(crop)`       | <font color="green">Yes</font> | <font color="green">Yes</font> | Calculates revenue and net profit per crop                                 |
| `crop_roi(crop)`                                | <font color="green">Yes</font> | <font color="green">Yes</font> | Profit per grow day ($(\text{revenue} - \text{cost}) / \text{grow\_days}$) |
| `best_crop()`                                   | <font color="green">Yes</font> |  <font color="red">No</font>   | Dynamically select crop with highest live ROI                              |
| `should_sell(item, threshold)`                  | <font color="green">Yes</font> | <font color="green">Yes</font> | Checks `inventory > 0` and price threshold                                 |
| `should_buy_seed(crop, target_count)`           | <font color="green">Yes</font> | <font color="green">Yes</font> | Checks `seeds < target_count` and affordability                            |
| `should_expand()`                               | <font color="green">Yes</font> | <font color="green">Yes</font> | Threshold check to buy land when `money > 5000`                            |
| `should_hire()`                                 | <font color="green">Yes</font> |  <font color="red">No</font>   | Trigger to hire extra farmhands when `money > 10000`                       |

---

### Agent Configuration (`src/agent/config.py`)

**Status**: <font color="green">Fully Integrated (100%)</font>

| Feature / Method             |          Implemented           |           In Planner           | Notes / Action                                                                            |
| :--------------------------- | :----------------------------: | :----------------------------: | :---------------------------------------------------------------------------------------- |
| `AgentConfig` dataclass      | <font color="green">Yes</font> | <font color="green">Yes</font> | Stores `target_crop`, `sell_threshold`, `seed_target`, `expand_land`, `max_hires_per_day` |
| `seed_cost`, `max_yield_day` | <font color="green">Yes</font> | <font color="green">Yes</font> | Property lookups derived from `CROPS` metadata table                                      |
| `DEFAULT_CONFIG`             | <font color="green">Yes</font> | <font color="green">Yes</font> | Default single-crop maximizer configuration instance (`MELON`)                            |

---

### Candidate Search (`src/agent/search.py`)

**Status**: <font color="green">Fully Integrated (100%)</font>

| Feature / Method                   |          Implemented           |           In Planner           | Notes / Action                                           |
| :--------------------------------- | :----------------------------: | :----------------------------: | :------------------------------------------------------- |
| `Node` dataclass                   | <font color="green">Yes</font> | <font color="green">Yes</font> | Wraps `score`, `action`, `state`, `parent`               |
| `Search.add(score, action)`        | <font color="green">Yes</font> | <font color="green">Yes</font> | Enqueues candidate action with utility score into pool   |
| `Search.topk(k)`                   | <font color="green">Yes</font> | <font color="green">Yes</font> | Extracts top-$k$ highest utility nodes sorted descending |
| `Search.best()`, `Search.choose()` | <font color="green">Yes</font> | <font color="green">Yes</font> | Returns best scoring node / action                       |
| `Search.clear()`, `Search.empty()` | <font color="green">Yes</font> | <font color="green">Yes</font> | Pool lifecycle management between decision turns         |
| `Search.dump()`                    | <font color="green">Yes</font> |  <font color="red">No</font>   | Debug utility for printing top candidate actions         |

---

### Actions (`src/environment/actions.py`)

**Status**: <font color="orange">Partially Integrated (~45%)</font>

| Category            | Method                       |          Implemented           |           In Planner           | Notes / Action                                    |
| :------------------ | :--------------------------- | :----------------------------: | :----------------------------: | :------------------------------------------------ |
| **Movement & Core** | `pass_turn()`                | <font color="green">Yes</font> | <font color="green">Yes</font> | Idle fallback (`["PASS"]`)                        |
|                     | `move(direction)`            | <font color="green">Yes</font> | <font color="green">Yes</font> | Directional movement (`score = 20-40`)            |
|                     | `merge(*actions)`            | <font color="green">Yes</font> | <font color="green">Yes</font> | Combines 1 farmer action + up to 10 market orders |
| **Farming**         | `harvest()`                  | <font color="green">Yes</font> | <font color="green">Yes</font> | Harvest mature crop (`score = 100 + value`)       |
|                     | `water()`                    | <font color="green">Yes</font> | <font color="green">Yes</font> | Water unwatered plant (`score = 80`)              |
|                     | `plant(crop)`                | <font color="green">Yes</font> | <font color="green">Yes</font> | Plant seed on empty tile (`score = 60 + roi`)     |
|                     | `dig()`                      | <font color="green">Yes</font> | <font color="green">Yes</font> | Clear weed on current tile (`score = 90`)         |
|                     | `fertilize()`                | <font color="green">Yes</font> |  <font color="red">No</font>   | Apply fertilizer for $+1$ bonus yield/day         |
| **Market Orders**   | `sell(item, amount)`         | <font color="green">Yes</font> | <font color="green">Yes</font> | Sell produce (`score = 50`)                       |
|                     | `buy_seed(crop, amount)`     | <font color="green">Yes</font> | <font color="green">Yes</font> | Buy seeds (`score = 40`)                          |
|                     | `buy_land(x, y)`             | <font color="green">Yes</font> | <font color="green">Yes</font> | Buy quadrant (`score = 100`)                      |
|                     | `hire_hand()`                | <font color="green">Yes</font> |  <font color="red">No</font>   | Hire worker when affordable                       |
|                     | `buy_product(item, amount)`  | <font color="green">Yes</font> |  <font color="red">No</font>   | Buy wheat / fertilizer                            |
|                     | `buy_animal(animal, amount)` | <font color="green">Yes</font> |  <font color="red">No</font>   | Buy Goose / Cow / Sheep                           |
| **Animals & Coops** | `build_coop()`               | <font color="green">Yes</font> |  <font color="red">No</font>   | Construct coop structure                          |
|                     | `build_pasture()`            | <font color="green">Yes</font> |  <font color="red">No</font>   | Construct pasture structure                       |
|                     | `feed()`                     | <font color="green">Yes</font> |  <font color="red">No</font>   | Feed animal with wheat                            |
|                     | `care()`                     | <font color="green">Yes</font> |  <font color="red">No</font>   | Pet / care for animal                             |
|                     | `collect_fertilizer()`       | <font color="green">Yes</font> |  <font color="red">No</font>   | Collect animal byproduct                          |
| **Shed Transfer**   | `pickup(item, amount)`       | <font color="green">Yes</font> |  <font color="red">No</font>   | Withdraw items from shed                          |
|                     | `place(item, amount)`        | <font color="green">Yes</font> |  <font color="red">No</font>   | Place animal or inventory                         |
|                     | `drop()`                     | <font color="green">Yes</font> |  <font color="red">No</font>   | Dump carried items into shed                      |

---

### Market Intelligence (`src/environment/market.py`)

**Status**: <font color="red">Unused in Planner (0%)</font>

| Feature / Method                                  |          Implemented           |         In Planner          | Notes / Action                                        |
| :------------------------------------------------ | :----------------------------: | :-------------------------: | :---------------------------------------------------- |
| `Market._history`, `_update()`                    | <font color="green">Yes</font> | <font color="red">No</font> | Stores last 20 turns of prices per good               |
| `reset_history()`                                 | <font color="green">Yes</font> | <font color="red">No</font> | Clears cached history across episodes/matches         |
| `average(item)`, `minimum(item)`, `maximum(item)` | <font color="green">Yes</font> | <font color="red">No</font> | Historical price statistical bounds                   |
| `trend(item)`                                     | <font color="green">Yes</font> | <font color="red">No</font> | Price trajectory slope over window                    |
| `normalized_price(item)`                          | <font color="green">Yes</font> | <font color="red">No</font> | Relative price index between min and max              |
| `expensive(item)`, `cheap(item)`                  | <font color="green">Yes</font> | <font color="red">No</font> | Sell at peaks ($\ge 0.80$) / buy at dips ($\le 0.20$) |
| `sell_score(item)`                                | <font color="green">Yes</font> | <font color="red">No</font> | Composite ranking for shed inventory sales            |
| `best_item_to_sell()`                             | <font color="green">Yes</font> | <font color="red">No</font> | Ranks all shed goods to pick optimal sale             |

---

### Multi-Unit Scheduler (`src/agent/scheduler.py`)

**Status**: <font color="red">Unused in Planner (0%)</font>

| Feature / Method                   |          Implemented           |         In Planner          | Action                                                                     |
| :--------------------------------- | :----------------------------: | :-------------------------: | :------------------------------------------------------------------------- |
| `Job` dataclass                    | <font color="green">Yes</font> | <font color="red">No</font> | Priority, action, target coordinates, actor                                |
| `add_job(...)`, `sort()`, `best()` | <font color="green">Yes</font> | <font color="red">No</font> | Priority job queue                                                         |
| `assign()`                         | <font color="green">Yes</font> | <font color="red">No</font> | Greedily assigns jobs to farmer and farmhands without coordinate collision |
| `clear()`                          | <font color="green">Yes</font> | <font color="red">No</font> | Reset job pool between turns                                               |

---

### Test Suite (`tests/`)

**Status**: <font color="orange">Needs Overhaul (~20%)</font>

| Test File / Area          |             Implemented             |              Status              | Action                                                                                |
| :------------------------ | :---------------------------------: | :------------------------------: | :------------------------------------------------------------------------------------ |
| `tests/test_planner.py`   | <font color="orange">Partial</font> | <font color="red">Failing</font> | Fix legacy fixture invocation and update mock state schema to match `GameState`       |
| `tests/test_state.py`     |     <font color="red">No</font>     | <font color="red">Missing</font> | Unit tests for `GameState` properties, coordinate getters, and observation parsing    |
| `tests/test_board.py`     |     <font color="red">No</font>     | <font color="red">Missing</font> | Unit tests for `Tile` getters, `Board` generators, `nearest()`, and `nearest_other()` |
| `tests/test_economy.py`   |     <font color="red">No</font>     | <font color="red">Missing</font> | Unit tests for crop ROI, profit, `best_crop()`, and threshold checks                  |
| `tests/test_market.py`    |     <font color="red">No</font>     | <font color="red">Missing</font> | Unit tests for price history, rolling trends, normalization, and `sell_score`         |
| `tests/test_actions.py`   |     <font color="red">No</font>     | <font color="red">Missing</font> | Unit tests for `ActionBuilder` factories and `merge()` logic                          |
| `tests/test_scheduler.py` |     <font color="red">No</font>     | <font color="red">Missing</font> | Unit tests for `Job` priority queue and non-colliding worker assignment               |
| `tests/test_search.py`    |     <font color="red">No</font>     | <font color="red">Missing</font> | Unit tests for `Search` node ranking, top-$k$, and clear lifecycle                    |

---
