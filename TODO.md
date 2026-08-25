# Jeremy Kaggriculture — Project Status & Roadmap (TODO)

This document tracks the implementation, integration status, and development roadmap for all modules, classes, and mechanics across the **Jeremy** codebase.

---

## Overall Module Integration in Planner

| Module / Subsystem                                         |           Implementation            |              Planner Integration               | Status & Responsibility                                                                                                                                          |
| :--------------------------------------------------------- | :---------------------------------: | :--------------------------------------------: | :--------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [`src/main.py`](src/main.py)                               | <font color="green">**100%**</font> |   <font color="green">**100% (Full)**</font>   | Kaggle entrypoint: exports `agent(obs)`, executes `Planner(state).play().to_dict()`                                                                              |
| [`src/environment/state.py`](src/environment/state.py)     | <font color="green">**100%**</font> |   <font color="green">**100% (Full)**</font>   | Typed observation wrapper dataclass, coordinates (`x`, `y`), price & inventory queries, financial affordability, quadrant and fertilizer checks                  |
| [`src/environment/board.py`](src/environment/board.py)     | <font color="green">**100%**</font> |   <font color="green">**100% (Full)**</font>   | Spatial grid, tile model (`Tile`), generators (`empty_tiles`, `plants`, `weeds`, `harvestable`, `needs_water`), navigation (`step_toward`, `manhattan_distance`) |
| [`src/environment/economy.py`](src/environment/economy.py) | <font color="green">**100%**</font> |   <font color="green">**100% (Full)**</font>   | ROI calculations, dynamic crop selection (`best_crop` with end-game horizon), `should_sell`, `should_buy_seed`, `should_expand`, `should_hire`, `hire_cost` |
| [`src/environment/actions.py`](src/environment/actions.py) | <font color="green">**100%**</font> | <font color="orange">**55% (Moderate)**</font> | Action factory (`move`, `harvest`, `water`, `plant`, `dig`, `fertilize`, `sell`, `buy_seed`, `buy_land`, `hire_hand`, `merge` actively used)                     |
| [`src/agent/config.py`](src/agent/config.py)               | <font color="green">**100%**</font> |   <font color="green">**100% (Full)**</font>   | Strategy configuration dataclass (`target_crop`, `sell_threshold`, `seed_target`, `expand_land`, `max_hires_per_day`, `dynamic_crops`, `get_crop`)        |
| [`src/agent/search.py`](src/agent/search.py)               | <font color="green">**100%**</font> |   <font color="green">**100% (Full)**</font>   | Scored candidate action pool (`Node`), top-$k$ sorting, decision selection for market orders & expansion                                                         |
| [`src/agent/scheduler.py`](src/agent/scheduler.py)         | <font color="green">**100%**</font> |   <font color="green">**100% (Full)**</font>   | Multi-unit spatial task dispatching for farmer + hired farmhands (`Job`, `add_job`, `extend_jobs`, `assign`) actively used in `Planner.play()`                   |
| [`src/agent/jobs.py`](src/agent/jobs.py)                   | <font color="green">**100%**</font> |   <font color="green">**100% (Full)**</font>   | Composable task pipeline (`harvest_jobs`, `water_jobs`, `weed_jobs`, `plant_jobs`, `schedule_jobs`) populating Scheduler each turn                               |
| [`src/agent/planner.py`](src/agent/planner.py)             | <font color="green">**100%**</font> |   <font color="green">**100% (Full)**</font>   | Turn decision coordinator orchestrating market heuristics, job scheduling, and multi-unit action synthesis                                                       |
| [`src/agent/heuristics/`](src/agent/heuristics/)           | <font color="green">**100%**</font> |   <font color="green">**100% (Full)**</font>   | Modular evaluator functions (`evaluate_market`, `evaluate_expansion`, `evaluate_farming`, `evaluate_movement`, `scores.py`)                                      |
| [`src/environment/market.py`](src/environment/market.py)   | <font color="green">**100%**</font> |   <font color="green">**100% (Full)**</font>   | Rolling 20-turn price history, trend indicators, normalized prices, `sell_score`, `best_item_to_sell` actively used in `evaluate_market()`                       |

---

## Detailed Module Breakdown & Integration

### State (`src/environment/state.py`)

**Status**: <font color="green">Fully Integrated (100%)</font>

| Feature / Method                     |          Implemented           |           In Planner           | Notes / Action                                                                                     |
| :----------------------------------- | :----------------------------: | :----------------------------: | :------------------------------------------------------------------------------------------------- |
| `GameState.from_obs(obs)`            | <font color="green">Yes</font> | <font color="green">Yes</font> | Factory method parsing raw observation dict into `GameState`                                       |
| `x`, `y`                             | <font color="green">Yes</font> | <font color="green">Yes</font> | Property aliases for farmer coordinates `farmer[0]`, `farmer[1]`                                   |
| `current_tile`                       | <font color="green">Yes</font> | <font color="green">Yes</font> | Returns raw tile content under the farmer (`tiles[y][x]`)                                          |
| `total_shed_inventory`               | <font color="green">Yes</font> | <font color="green">Yes</font> | Sum of all stored non-seed items in shed                                                           |
| `is_quadrant_unlocked(quadrant)`     | <font color="green">Yes</font> | <font color="green">Yes</font> | Checks if specific quadrant (`NW`, `NE`, `SW`, `SE`) is unlocked                                   |
| `is_tile_unlocked(x, y)`             | <font color="green">Yes</font> | <font color="green">Yes</font> | Coordinate-level unlocked quadrant boundary validation                                             |
| `price(item)`                        | <font color="green">Yes</font> | <font color="green">Yes</font> | Market price lookup (`prices.get(item, 0)`)                                                        |
| `inventory(item)`                    | <font color="green">Yes</font> | <font color="green">Yes</font> | Shed inventory count (`shed.get(item, 0)`)                                                         |
| `seed_count(crop)`, `has_seed(crop)` | <font color="green">Yes</font> | <font color="green">Yes</font> | Seed inventory queries (`seeds.get(crop, 0)`)                                                      |
| `can_afford(amount)`                 | <font color="green">Yes</font> | <font color="green">Yes</font> | Checks `money >= amount`                                                                           |
| `has_fertilizer()`                   | <font color="green">Yes</font> | <font color="green">Yes</font> | Checks if shed inventory contains fertilizer                                                       |
| `step`, `day`, `hour`, `player`      | <font color="green">Yes</font> | <font color="green">Yes</font> | Core temporal and agent identification fields                                                      |
| `unlocked_quadrants`                 | <font color="green">Yes</font> | <font color="green">Yes</font> | Track unlocked quadrants (`NW`, `NE`, `SW`, `SE`), active in Board generators and expansion checks |
| `hands`, `hires_today`               | <font color="green">Yes</font> | <font color="green">Yes</font> | Active farmhand positions and daily hire counter used for multi-unit dispatch & hiring limits      |

---

### Board (`src/environment/board.py`)

**Status**: <font color="green">Fully Integrated (100%)</font>

| Feature / Method                                                                                           |          Implemented           |           In Planner           | Notes / Action                                                                               |
| :--------------------------------------------------------------------------------------------------------- | :----------------------------: | :----------------------------: | :------------------------------------------------------------------------------------------- |
| `step_toward(fx, fy, tx, ty)`                                                                              | <font color="green">Yes</font> | <font color="green">Yes</font> | Shared cardinal direction pathfinding utility across movement, scheduler, and bot baselines  |
| `manhattan_distance(x1, y1, x2, y2)`                                                                       | <font color="green">Yes</font> | <font color="green">Yes</font> | Optimized distance calculation function used in tile queries and scheduler utility scoring   |
| `Tile` properties (`pos`, `empty`, `is_plant`, `is_weed`, `crop`, `watered`, `yield_units`, `planted_day`) | <font color="green">Yes</font> | <font color="green">Yes</font> | Encapsulates single tile attributes and status checks                                        |
| `Tile.age(current_day)`                                                                                    | <font color="green">Yes</font> | <font color="green">Yes</font> | Calculates days elapsed since planting                                                       |
| `Tile.is_ripe(current_day)`                                                                                | <font color="green">Yes</font> | <font color="green">Yes</font> | Checks if plant age $\ge$ `max_yield_day` and `yield_units > 0`                              |
| `Tile.distance(x, y)`                                                                                      | <font color="green">Yes</font> | <font color="green">Yes</font> | Computes Manhattan distance to target coordinates                                            |
| `Tile.is_fertilized(current_day)`                                                                          | <font color="green">Yes</font> | <font color="green">Yes</font> | Checks if tile has active fertilizer coverage for current day                                |
| `Tile.is_unlocked(unlocked_quadrants)`                                                                     | <font color="green">Yes</font> | <font color="green">Yes</font> | Validates whether tile resides in unlocked quadrant                                          |
| `Board.get_tile(x, y)`                                                                                     | <font color="green">Yes</font> | <font color="green">Yes</font> | Retrieves tile at coordinate if within grid bounds                                           |
| `all_tiles()`, `empty_tiles()`, `plants()`                                                                 | <font color="green">Yes</font> | <font color="green">Yes</font> | Grid generators for broad spatial iteration (`empty_tiles` supports `only_unlocked=True`)    |
| `crops(crop)`                                                                                              | <font color="green">Yes</font> | <font color="green">Yes</font> | Filter plant tiles by specific crop type                                                     |
| `weeds(only_unlocked=True)`                                                                                | <font color="green">Yes</font> | <font color="green">Yes</font> | Yields weed tiles on unlocked quadrants; evaluated in `evaluate_movement` for weed navigation|
| `harvestable(crop)`, `needs_water(crop)`                                                                   | <font color="green">Yes</font> | <font color="green">Yes</font> | Target generators with optional crop filtering                                               |
| `nearest(tiles)`                                                                                           | <font color="green">Yes</font> | <font color="green">Yes</font> | Finds closest matching tile to the farmer                                                    |
| `nearest_other(tiles)`                                                                                     | <font color="green">Yes</font> | <font color="green">Yes</font> | Finds closest tile excluding the farmer's current coordinates                                |
| `nearest_to(x, y, tiles, exclude_pos)`                                                                     | <font color="green">Yes</font> | <font color="green">Yes</font> | General distance minimizer from arbitrary coordinate $(x, y)$                                |

---

### Economy (`src/environment/economy.py`)

**Status**: <font color="green">Fully Integrated (100%)</font>

| Feature / Method                                |          Implemented           |           In Planner           | Notes / Action                                                                                             |
| :---------------------------------------------- | :----------------------------: | :----------------------------: | :--------------------------------------------------------------------------------------------------------- |
| `price(item)`, `inventory(item)`, `seeds(crop)` | <font color="green">Yes</font> | <font color="green">Yes</font> | Delegates queries to underlying `GameState`                                                                |
| `crop_cost(crop)`, `crop_grow_days(crop)`       | <font color="green">Yes</font> | <font color="green">Yes</font> | Metadata lookups from official `CROPS` dictionary                                                          |
| `crop_revenue(crop)`, `crop_profit(crop)`       | <font color="green">Yes</font> | <font color="green">Yes</font> | Calculates revenue and net profit per crop                                                                 |
| `crop_roi(crop)`                                | <font color="green">Yes</font> | <font color="green">Yes</font> | Profit per grow day ($(\text{revenue} - \text{cost}) / \text{grow\_days}$)                                 |
| `best_crop()`                                   | <font color="green">Yes</font> | <font color="green">Yes</font> | Dynamically selects crop with highest live ROI and end-game horizon filter (active via `AgentConfig.get_crop`) |
| `should_sell(item, threshold)`                  | <font color="green">Yes</font> | <font color="green">Yes</font> | Checks `inventory > 0` and price threshold                                                                 |
| `should_buy_seed(crop, target_count)`           | <font color="green">Yes</font> | <font color="green">Yes</font> | Checks `seeds < target_count` and affordability                                                            |
| `expansion_cost()`, `next_quadrant_target()`    | <font color="green">Yes</font> | <font color="green">Yes</font> | Determines price and target coordinate for next quadrant unlock                                            |
| `should_expand()`                               | <font color="green">Yes</font> | <font color="green">Yes</font> | Threshold check to buy land when `money >= cost + 300`                                                     |
| `hire_cost()`                                   | <font color="green">Yes</font> | <font color="green">Yes</font> | Fibonacci daily hiring cost based on `hires_today`                                                         |
| `should_hire(max_hires_per_day)`                | <font color="green">Yes</font> | <font color="green">Yes</font> | High-priority hiring trigger evaluated in `evaluate_market`                                                |

---

### Task Generation Pipeline (`src/agent/jobs.py`)

**Status**: <font color="green">Fully Integrated (100%)</font>

| Feature / Generator                      |          Implemented           |           In Planner           | Description                                                                                     |
| :--------------------------------------- | :----------------------------: | :----------------------------: | :---------------------------------------------------------------------------------------------- |
| `harvest_jobs(planner, crop)`            | <font color="green">Yes</font> | <font color="green">Yes</font> | Generates `HARVEST` jobs scored by `HARVEST_BASE + (yield * price)`                             |
| `water_jobs(planner, crop)`              | <font color="green">Yes</font> | <font color="green">Yes</font> | Generates `WATER` jobs for thirsty plants scored by `WATER`                                     |
| `weed_jobs(planner, crop)`               | <font color="green">Yes</font> | <font color="green">Yes</font> | Generates `DIG` jobs for weeds on unlocked tiles scored by `DIG_WEED`                           |
| `plant_jobs(planner, crop)`              | <font color="green">Yes</font> | <font color="green">Yes</font> | Generates `PLANT` jobs for empty unlocked tiles scored by `PLANT_BASE + ROI`                    |
| `DEFAULT_JOB_PIPELINE`                   | <font color="green">Yes</font> | <font color="green">Yes</font> | Composable tuple of active job generators                                                       |
| `schedule_jobs(planner, crop, pipeline)` | <font color="green">Yes</font> | <font color="green">Yes</font> | Clears scheduler, executes generator pipeline, and populates `scheduler.jobs` in `Planner.play` |

---

### Multi-Unit Scheduler (`src/agent/scheduler.py`)

**Status**: <font color="green">Fully Integrated (100%)</font>

| Feature / Method                    |          Implemented           |           In Planner           | Description                                                                             |
| :---------------------------------- | :----------------------------: | :----------------------------: | :-------------------------------------------------------------------------------------- |
| `Job` dataclass                     | <font color="green">Yes</font> | <font color="green">Yes</font> | Pure data container (`priority`, `action`, `target`, `actor`, `item`) with `slots=True` |
| `default_utility_scorer(job, x, y)` | <font color="green">Yes</font> | <font color="green">Yes</font> | Distance-discounted utility scoring: $\text{priority} - 2.0 \times \text{distance}$     |
| `job_to_action(job, x, y)`          | <font color="green">Yes</font> | <font color="green">Yes</font> | Formats movement steps or tile executions via `ActionBuilder`                           |
| `add_job(...)`, `extend_jobs(...)`  | <font color="green">Yes</font> | <font color="green">Yes</font> | Ingests individual or batched jobs into candidate pool                                  |
| `_assign_one(x, y, used)`           | <font color="green">Yes</font> | <font color="green">Yes</font> | Selects optimal available job using C-level `max()` with injected scorer                |
| `assign()`                          | <font color="green">Yes</font> | <font color="green">Yes</font> | Dispatches non-colliding jobs to `state.farmer` + `state.hands`, returning action lists |
| `clear()`                           | <font color="green">Yes</font> | <font color="green">Yes</font> | Resets job pool each turn                                                               |

---

### Actions (`src/environment/actions.py`)

**Status**: <font color="orange">Partially Integrated (~55%)</font>

| Category            | Method                       |          Implemented           |           In Planner           | Notes / Action                                           |
| :------------------ | :--------------------------- | :----------------------------: | :----------------------------: | :------------------------------------------------------- |
| **Movement & Core** | `pass_turn()`                | <font color="green">Yes</font> | <font color="green">Yes</font> | Idle fallback (`["PASS"]`)                               |
|                     | `move(direction)`            | <font color="green">Yes</font> | <font color="green">Yes</font> | Directional movement (`score = 20-40`)                   |
|                     | `merge(*actions)`            | <font color="green">Yes</font> | <font color="green">Yes</font> | Combines 1 farmer action + up to 10 market orders        |
| **Farming**         | `harvest()`                  | <font color="green">Yes</font> | <font color="green">Yes</font> | Harvest mature crop (`score = 100 + value`)              |
|                     | `water()`                    | <font color="green">Yes</font> | <font color="green">Yes</font> | Water unwatered plant (`score = 80`)                     |
|                     | `plant(crop)`                | <font color="green">Yes</font> | <font color="green">Yes</font> | Plant seed on empty tile (`score = 60 + roi`)            |
|                     | `dig()`                      | <font color="green">Yes</font> | <font color="green">Yes</font> | Clear weed on current tile (`score = 90`)                |
|                     | `fertilize()`                | <font color="green">Yes</font> | <font color="green">Yes</font> | Apply fertilizer for $+1$ bonus yield/day (`score = 40`) |
| **Market Orders**   | `sell(item, amount)`         | <font color="green">Yes</font> | <font color="green">Yes</font> | Sell produce (`score = 50`)                              |
|                     | `buy_seed(crop, amount)`     | <font color="green">Yes</font> | <font color="green">Yes</font> | Buy seeds (`score = 45`)                                 |
|                     | `buy_land(x, y)`             | <font color="green">Yes</font> | <font color="green">Yes</font> | Buy quadrant (`score = 110`)                             |
|                     | `hire_hand()`                | <font color="green">Yes</font> | <font color="green">Yes</font> | Hire worker when affordable (`score = 95`)               |
|                     | `buy_product(item, amount)`  | <font color="green">Yes</font> |  <font color="red">No</font>   | Buy wheat / fertilizer                                   |
|                     | `buy_animal(animal, amount)` | <font color="green">Yes</font> |  <font color="red">No</font>   | Buy Goose / Cow / Sheep                                  |
| **Animals & Coops** | `build_coop()`               | <font color="green">Yes</font> |  <font color="red">No</font>   | Construct coop structure                                 |
|                     | `build_pasture()`            | <font color="green">Yes</font> |  <font color="red">No</font>   | Construct pasture structure                              |
|                     | `feed()`                     | <font color="green">Yes</font> |  <font color="red">No</font>   | Feed animal with wheat                                   |
|                     | `care()`                     | <font color="green">Yes</font> |  <font color="red">No</font>   | Pet / care for animal                                    |
|                     | `collect_fertilizer()`       | <font color="green">Yes</font> |  <font color="red">No</font>   | Collect animal byproduct                                 |
| **Shed Transfer**   | `pickup(item, amount)`       | <font color="green">Yes</font> |  <font color="red">No</font>   | Withdraw items from shed                                 |
|                     | `place(item, amount)`        | <font color="green">Yes</font> |  <font color="red">No</font>   | Place animal or inventory                                |
|                     | `drop()`                     | <font color="green">Yes</font> |  <font color="red">No</font>   | Dump carried items into shed                             |

---

### Market Intelligence (`src/environment/market.py`)

**Status**: <font color="green">Fully Integrated (100%)</font>

| Feature / Method                                  |          Implemented           |           In Planner           | Notes / Action                                                                                       |
| :------------------------------------------------ | :----------------------------: | :----------------------------: | :--------------------------------------------------------------------------------------------------- |
| `Market.history`, `_update()`                     | <font color="green">Yes</font> | <font color="green">Yes</font> | Stores rolling 20-turn price window per good, refreshed every turn                                   |
| `reset_history()`                                 | <font color="green">Yes</font> | <font color="green">Yes</font> | Clears cached history across episodes/matches                                                        |
| `average(item)`, `minimum(item)`, `maximum(item)` | <font color="green">Yes</font> | <font color="green">Yes</font> | Historical price statistical bounds                                                                  |
| `trend(item)`                                     | <font color="green">Yes</font> | <font color="green">Yes</font> | Price trajectory slope over window                                                                   |
| `normalized_price(item)`                          | <font color="green">Yes</font> | <font color="green">Yes</font> | Relative price index between min and max                                                             |
| `expensive(item)`, `cheap(item)`                  | <font color="green">Yes</font> | <font color="green">Yes</font> | Threshold flags for peaks ($\ge 0.80$) / dips ($\le 0.20$)                                           |
| `sell_score(item)`                                | <font color="green">Yes</font> | <font color="green">Yes</font> | Composite ranking for shed inventory sales based on live price, trend, and peak normalization        |
| `best_item_to_sell()`                             | <font color="green">Yes</font> | <font color="green">Yes</font> | Ranks all shed goods to pick optimal product to liquidate, actively evaluated in `evaluate_market()` |

---
