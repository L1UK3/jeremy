# Jeremy Kaggriculture — Project Status & Roadmap (TODO)

This document tracks the implementation, integration status, and roadmap for all modules, classes, and mechanics across the **Jeremy** codebase.

---

## 1. Overall Module Integration Summary

| Module / Subsystem                                                   |           Implementation            |              Planner Integration               | Status & Responsibility                                                                                   |
| :------------------------------------------------------------------- | :---------------------------------: | :--------------------------------------------: | :-------------------------------------------------------------------------------------------------------- |
| [`src/main.py`](src/main.py)                                         | <font color="green">**100%**</font> |   <font color="green">**100% (Full)**</font>   | Kaggle entrypoint: exports `agent(obs)`, executes `Planner(state).play().to_dict()`                       |
| [`src/environment/state.py`](src/environment/state.py)               | <font color="green">**100%**</font> |   <font color="green">**100% (Full)**</font>   | Typed observation wrapper, coordinate getters (`x`, `y`), price & inventory queries                       |
| [`src/environment/board.py`](src/environment/board.py)               | <font color="green">**100%**</font> |   <font color="green">**85% (High)**</font>    | Spatial grid, tile generators (`empty_tiles`, `harvestable`, `needs_water`, `weeds`), Manhattan distance  |
| [`src/environment/economy.py`](src/environment/economy.py)           | <font color="green">**100%**</font> |   <font color="green">**75% (High)**</font>    | ROI calculations, crop selection, `should_sell`, `should_buy_seed`, `should_expand`                       |
| [`src/environment/actions.py`](src/environment/actions.py)           | <font color="green">**100%**</font> | <font color="orange">**45% (Moderate)**</font> | Action factory (`move`, `harvest`, `water`, `plant`, `dig`, `sell`, `buy_seed`, `buy_land`, `merge` used) |
| [`src/agent/config.py`](src/agent/config.py)                         | <font color="green">**100%**</font> |   <font color="green">**100% (Full)**</font>   | Strategy configuration constants (`target_crop`, `sell_threshold`, `seed_target`, `expand_land`)          |
| [`src/agent/search.py`](src/agent/search.py)                         | <font color="green">**100%**</font> |   <font color="green">**100% (Full)**</font>   | Scored candidate action pool, top-$k$ sorting, decision selection                                         |
| [`src/agent/planner.py`](src/agent/planner.py)                       | <font color="green">**100%**</font> |   <font color="green">**100% (Full)**</font>   | Turn decision coordinator (evaluates market, current tile, planting, movement, expansion)                 |
| [`src/environment/market.py`](src/environment/market.py)             | <font color="green">**100%**</font> |    <font color="red">**0% (Unused)**</font>    | Rolling 20-turn price history, trend indicators, normalized prices, `sell_score`                          |
| [`src/agent/scheduler.py`](src/agent/scheduler.py)                   | <font color="green">**100%**</font> |    <font color="red">**0% (Unused)**</font>    | Multi-unit spatial task dispatching for farmer + hired farmhands                                          |
| [`simulation/episode.py`](simulation/episode.py)                     | <font color="green">**100%**</font> |  <font color="green">**N/A (Harness)**</font>  | 720-turn match simulator between 2 agents, seat alternator, replay JSON exporter                          |
| [`simulation/base/melon_maxxer.py`](simulation/base/melon_maxxer.py) | <font color="green">**100%**</font> | <font color="green">**N/A (Baseline)**</font>  | Reference baseline agent for benchmarking                                                                 |
| [`scripts/build_submission.py`](scripts/build_submission.py)         | <font color="green">**100%**</font> |   <font color="green">**N/A (Tool)**</font>    | Bundles modular code into standalone `submission.py` or `submission.tar.gz`                               |
| [`data/`](data/) (Archive Pipeline)                                  | <font color="green">**100%**</font> |   <font color="green">**N/A (Data)**</font>    | Kaggle replay scraper (`scrape.py`), Parquet repackager (`repack.py`), feature extractor (`features.py`)  |
| [`tests/`](tests/) (Test Suite)                                      | <font color="orange">**30%**</font> |      <font color="red">**Broken**</font>       | Unit test suite (legacy fixture structure requires overhaul)                                              |

---

## 2. Detailed Module Breakdown & Integration

### State (`src/environment/state.py`)

- **Status**: <font color="green">Fully Integrated (100%)</font>
- **Purpose**: Typed dataclass wrapping raw Kaggle observation dicts.

| Feature / Method                     |          Implemented           |           In Planner           | Notes / Action Item                          |
| :----------------------------------- | :----------------------------: | :----------------------------: | :------------------------------------------- |
| `GameState.from_obs(obs)`            | <font color="green">Yes</font> | <font color="green">Yes</font> | Parses raw observation into structured state |
| `x`, `y`                             | <font color="green">Yes</font> | <font color="green">Yes</font> | Properties alias `farmer[0]`, `farmer[1]`    |
| `current_tile`                       | <font color="green">Yes</font> | <font color="green">Yes</font> | Returns tile under farmer (`tiles[y][x]`)    |
| `price(item)`, `inventory(item)`     | <font color="green">Yes</font> | <font color="green">Yes</font> | Fetches market prices and shed stock         |
| `seed_count(crop)`, `has_seed(crop)` | <font color="green">Yes</font> | <font color="green">Yes</font> | Fast checks on seed storage                  |
| `can_afford(amount)`                 | <font color="green">Yes</font> | <font color="green">Yes</font> | Checks `money >= amount`                     |

---

### Board (`src/environment/board.py`)

- **Status**: <font color="green">Mostly Integrated (~85%)</font>
- **Purpose**: Tile wrappers, generators, and Manhattan distance pathfinding.

| Feature / Method                                                                                    |          Implemented           |           In Planner           | Notes / Action Item                              |
| :-------------------------------------------------------------------------------------------------- | :----------------------------: | :----------------------------: | :----------------------------------------------- |
| `Tile` properties (`empty`, `is_plant`, `is_weed`, `crop`, `watered`, `yield_units`, `planted_day`) | <font color="green">Yes</font> | <font color="green">Yes</font> | Encapsulates single tile attributes              |
| `Tile.distance(x, y)`                                                                               | <font color="green">Yes</font> | <font color="green">Yes</font> | Manhattan distance calculation                   |
| `all_tiles()`, `empty_tiles()`, `plants()`                                                          | <font color="green">Yes</font> | <font color="green">Yes</font> | Grid generators for target matching              |
| `harvestable(crop)`, `needs_water(crop)`                                                            | <font color="green">Yes</font> | <font color="green">Yes</font> | Target generators with optional crop filtering   |
| `nearest(tiles)`                                                                                    | <font color="green">Yes</font> | <font color="green">Yes</font> | Finds closest matching tile to the farmer        |
| `crops(crop)`                                                                                       | <font color="green">Yes</font> | <font color="green">Yes</font> | Filter tiles by specific crop type               |
| `weeds()`                                                                                           | <font color="green">Yes</font> |  <font color="red">No</font>   | **TODO**: Target distant weeds during idle turns |

---

### Economy (`src/environment/economy.py`)

- **Status**: <font color="green">Mostly Integrated (~75%)</font>
- **Purpose**: Financial calculations, profit per day (ROI), crop selection, affordability.

| Feature / Method                                |          Implemented           |           In Planner           | Notes / Action Item                                            |
| :---------------------------------------------- | :----------------------------: | :----------------------------: | :------------------------------------------------------------- |
| `price(item)`, `inventory(item)`, `seeds(crop)` | <font color="green">Yes</font> | <font color="green">Yes</font> | Query state properties                                         |
| `crop_cost(crop)`, `crop_grow_days(crop)`       | <font color="green">Yes</font> | <font color="green">Yes</font> | Lookups from `CROPS` table                                     |
| `crop_revenue(crop)`, `crop_profit(crop)`       | <font color="green">Yes</font> | <font color="green">Yes</font> | Calculates revenue and net profit per crop                     |
| `crop_roi(crop)`                                | <font color="green">Yes</font> | <font color="green">Yes</font> | Profit per grow day for crop prioritization                    |
| `should_sell(item, threshold)`                  | <font color="green">Yes</font> | <font color="green">Yes</font> | Checks `inventory > 0` and price threshold                     |
| `should_buy_seed(crop, target_count)`           | <font color="green">Yes</font> | <font color="green">Yes</font> | Checks `seeds < target_count` and affordability                |
| `should_expand()`                               | <font color="green">Yes</font> | <font color="green">Yes</font> | Trigger to buy land when `money > 5000`                        |
| `best_crop()`                                   | <font color="green">Yes</font> |  <font color="red">No</font>   | **TODO**: Dynamically select crop with highest live ROI        |
| `should_hire()`                                 | <font color="green">Yes</font> |  <font color="red">No</font>   | **TODO**: Trigger to hire extra farmhands when `money > 10000` |

---

### Agent Configuration (`src/agent/config.py`)

- **Status**: <font color="green">Fully Integrated (100%)</font>
- **Purpose**: High-level strategy constants and parameters.

| Feature / Method             |          Implemented           |           In Planner           | Notes / Action Item                                                                       |
| :--------------------------- | :----------------------------: | :----------------------------: | :---------------------------------------------------------------------------------------- |
| `AgentConfig` dataclass      | <font color="green">Yes</font> | <font color="green">Yes</font> | Stores `target_crop`, `sell_threshold`, `seed_target`, `expand_land`, `max_hires_per_day` |
| `seed_cost`, `max_yield_day` | <font color="green">Yes</font> | <font color="green">Yes</font> | Derived directly from `CROPS` metadata table                                              |
| `DEFAULT_CONFIG`             | <font color="green">Yes</font> | <font color="green">Yes</font> | Default single-crop maximizer configuration instance                                      |

---

### Candidate Search (`src/agent/search.py`)

- **Status**: <font color="green">Fully Integrated (100%)</font>
- **Purpose**: Scored candidate action pool, top-$k$ sorting, decision selection.

| Feature / Method                   |          Implemented           |           In Planner           | Notes / Action Item                        |
| :--------------------------------- | :----------------------------: | :----------------------------: | :----------------------------------------- |
| `Node` dataclass                   | <font color="green">Yes</font> | <font color="green">Yes</font> | Wraps `score`, `action`, `state`, `parent` |
| `Search.add(score, action)`        | <font color="green">Yes</font> | <font color="green">Yes</font> | Enqueues candidate actions into pool       |
| `Search.topk(k)`                   | <font color="green">Yes</font> | <font color="green">Yes</font> | Extracts top-$k$ highest utility actions   |
| `Search.best()`, `Search.choose()` | <font color="green">Yes</font> | <font color="green">Yes</font> | Returns best action from pool              |
| `Search.clear()`, `Search.empty()` | <font color="green">Yes</font> | <font color="green">Yes</font> | Search pool lifecycle management           |

---

### Actions (`src/environment/actions.py`)

- **Status**: <font color="orange">Partially Integrated (~45%)</font>
- **Purpose**: Standardized action builders for all game interactions.

| Category            | Method                       |          Implemented           |           In Planner           | Action Item / Target Utility                        |
| :------------------ | :--------------------------- | :----------------------------: | :----------------------------: | :-------------------------------------------------- |
| **Movement & Core** | `pass_turn()`                | <font color="green">Yes</font> | <font color="green">Yes</font> | Idle fallback                                       |
|                     | `move(direction)`            | <font color="green">Yes</font> | <font color="green">Yes</font> | Directional movement (`score = 20-40`)              |
|                     | `merge(*actions)`            | <font color="green">Yes</font> | <font color="green">Yes</font> | Combines 1 farmer action + market orders            |
| **Farming**         | `harvest()`                  | <font color="green">Yes</font> | <font color="green">Yes</font> | Harvest mature crop (`score = 100 + value`)         |
|                     | `water()`                    | <font color="green">Yes</font> | <font color="green">Yes</font> | Water unwatered plant (`score = 80`)                |
|                     | `plant(crop)`                | <font color="green">Yes</font> | <font color="green">Yes</font> | Plant highest-ROI seed (`score = 60 + roi`)         |
|                     | `dig()`                      | <font color="green">Yes</font> | <font color="green">Yes</font> | Clear weeds on current tile (`score = 90`)          |
|                     | `fertilize()`                | <font color="green">Yes</font> |  <font color="red">No</font>   | **TODO**: Apply fertilizer for $+1$ bonus yield/day |
| **Market Orders**   | `sell(item, amount)`         | <font color="green">Yes</font> | <font color="green">Yes</font> | Sell produce (`score = 50`)                         |
|                     | `buy_seed(crop, amount)`     | <font color="green">Yes</font> | <font color="green">Yes</font> | Buy seeds (`score = 40`)                            |
|                     | `buy_land(x, y)`             | <font color="green">Yes</font> | <font color="green">Yes</font> | Buy quadrant (`score = 100`)                        |
|                     | `hire_hand()`                | <font color="green">Yes</font> |  <font color="red">No</font>   | **TODO**: Hire worker when affordable               |
|                     | `buy_product(item, amount)`  | <font color="green">Yes</font> |  <font color="red">No</font>   | **TODO**: Buy wheat / fertilizer                    |
|                     | `buy_animal(animal, amount)` | <font color="green">Yes</font> |  <font color="red">No</font>   | **TODO**: Buy Goose / Cow / Sheep                   |
| **Animals & Coops** | `build_coop()`               | <font color="green">Yes</font> |  <font color="red">No</font>   | **TODO**: Construct coop structure                  |
|                     | `build_pasture()`            | <font color="green">Yes</font> |  <font color="red">No</font>   | **TODO**: Construct pasture structure               |
|                     | `feed()`                     | <font color="green">Yes</font> |  <font color="red">No</font>   | **TODO**: Feed animal with wheat                    |
|                     | `care()`                     | <font color="green">Yes</font> |  <font color="red">No</font>   | **TODO**: Pet / care for animal                     |
|                     | `collect_fertilizer()`       | <font color="green">Yes</font> |  <font color="red">No</font>   | **TODO**: Collect animal byproduct                  |
| **Shed Transfer**   | `pickup(item, amount)`       | <font color="green">Yes</font> |  <font color="red">No</font>   | **TODO**: Withdraw items from shed                  |
|                     | `place(item, amount)`        | <font color="green">Yes</font> |  <font color="red">No</font>   | **TODO**: Place animal or inventory                 |
|                     | `drop()`                     | <font color="green">Yes</font> |  <font color="red">No</font>   | **TODO**: Dump carried items into shed              |

---

### Planner Decision Engine (`src/agent/planner.py`)

- **Status**: <font color="green">Operational Baseline (~60% Feature Coverage)</font>
- **Purpose**: Evaluates market conditions, current tile state, planting opportunities, unit navigation, and expansion.

| Method                    |          Implemented           |               Status                | Current Behavior / Next Step                                                                                        |
| :------------------------ | :----------------------------: | :---------------------------------: | :------------------------------------------------------------------------------------------------------------------ |
| `evaluate_market()`       | <font color="green">Yes</font> | <font color="orange">Partial</font> | Sells target crop at fixed threshold; buys seed if `count < seed_target`. Needs `Market` rolling trend integration. |
| `evaluate_current_tile()` | <font color="green">Yes</font> | <font color="orange">Partial</font> | Digs weeds, harvests ripe target crop, waters unwatered plant. Needs fertilizer & multi-crop support.               |
| `evaluate_planting()`     | <font color="green">Yes</font> | <font color="orange">Partial</font> | Plants `target_crop` if seed available. Needs dynamic crop selection (`best_crop()`).                               |
| `evaluate_movement()`     | <font color="green">Yes</font> | <font color="orange">Partial</font> | Moves to nearest harvestable, thirsty plant, or empty tile. Needs weed pathfinding and multi-unit support.          |
| `evaluate_expansion()`    | <font color="green">Yes</font> | <font color="orange">Partial</font> | Buys land when `money > 5000`. Needs smart quadrant prioritization (`NE`/`SW`/`SE`).                                |
| `move_to(tile)`           | <font color="green">Yes</font> |  <font color="green">Active</font>  | Greedy Manhattan navigation toward target coordinates                                                               |
| `choose()`                | <font color="green">Yes</font> |  <font color="green">Active</font>  | Merges highest-scoring candidate actions                                                                            |
| `play()`                  | <font color="green">Yes</font> |  <font color="green">Active</font>  | Main per-turn pipeline execution                                                                                    |

---

### Market Intelligence (`src/environment/market.py`)

- **Status**: <font color="red">Unused in Planner (0%)</font>
- **Purpose**: Price history tracking, normalization, rolling average/trend, and composite sell score.

| Feature / Method                                  |          Implemented           |         In Planner          | Action Item                                           |
| :------------------------------------------------ | :----------------------------: | :-------------------------: | :---------------------------------------------------- |
| `Market._history`, `_update()`                    | <font color="green">Yes</font> | <font color="red">No</font> | Stores last 20 turns of prices per good               |
| `average(item)`, `minimum(item)`, `maximum(item)` | <font color="green">Yes</font> | <font color="red">No</font> | Historical price statistical bounds                   |
| `trend(item)`                                     | <font color="green">Yes</font> | <font color="red">No</font> | Price trajectory slope over window                    |
| `normalized_price(item)`                          | <font color="green">Yes</font> | <font color="red">No</font> | Relative price index between min and max              |
| `expensive(item)`, `cheap(item)`                  | <font color="green">Yes</font> | <font color="red">No</font> | Sell at peaks ($\ge 0.80$) / buy at dips ($\le 0.20$) |
| `sell_score(item)`                                | <font color="green">Yes</font> | <font color="red">No</font> | Composite ranking for shed inventory sales            |
| `best_item_to_sell()`                             | <font color="green">Yes</font> | <font color="red">No</font> | Ranks all shed goods to pick optimal sale             |

---

### Multi-Unit Scheduler (`src/agent/scheduler.py`)

- **Status**: <font color="red">Unused in Planner (0%)</font>
- **Purpose**: Spatial task allocation preventing conflicting unit movements/actions.

| Feature / Method                   |          Implemented           |         In Planner          | Action Item                                                                |
| :--------------------------------- | :----------------------------: | :-------------------------: | :------------------------------------------------------------------------- |
| `Job` dataclass                    | <font color="green">Yes</font> | <font color="red">No</font> | Priority, action, target coordinates, actor                                |
| `add_job(...)`, `sort()`, `best()` | <font color="green">Yes</font> | <font color="red">No</font> | Priority job queue                                                         |
| `assign()`                         | <font color="green">Yes</font> | <font color="red">No</font> | Greedily assigns jobs to farmer and farmhands without coordinate collision |
| `clear()`                          | <font color="green">Yes</font> | <font color="red">No</font> | Reset job pool between turns                                               |

---

### Simulation & Benchmarking (`simulation/`)

- **Status**: <font color="green">Operational (100%)</font>
- **Purpose**: 2-player head-to-head match runner, seat alternation, replay JSON export.

| Component                                            |          Implemented           |              Status               | Notes / Action Item                                                                  |
| :--------------------------------------------------- | :----------------------------: | :-------------------------------: | :----------------------------------------------------------------------------------- |
| `simulation/episode.py` (`Episode`, `EpisodeResult`) | <font color="green">Yes</font> | <font color="green">Active</font> | Runs 720-turn matches against baselines or other agents; exports replays             |
| `simulation/base/melon_maxxer.py`                    | <font color="green">Yes</font> | <font color="green">Active</font> | Standard reference baseline for local benchmarking                                   |
| Multi-Game Tournament Runner                         |  <font color="red">No</font>   | <font color="red">Planned</font>  | **TODO**: Script to run $N$-match tournament with alternating seats and Elo tracking |

---

### Build & Packaging (`scripts/build_submission.py`)

- **Status**: <font color="green">Operational (100%)</font>
- **Purpose**: Standalone submission file generator and archive bundler.

| Feature / Command                |          Implemented           |              Status               | Notes                                                                               |
| :------------------------------- | :----------------------------: | :-------------------------------: | :---------------------------------------------------------------------------------- |
| `--build` (`submission.py`)      | <font color="green">Yes</font> | <font color="green">Active</font> | Combines `agent/`, `environment/`, `main.py` into a single standalone Python script |
| `--bundle` (`submission.tar.gz`) | <font color="green">Yes</font> | <font color="green">Active</font> | Packages clean source tree without `__pycache__` for Kaggle tarball submissions     |

---

### Public Ladder Archive Pipeline (`data/`)

- **Status**: <font color="green">Operational (100%)</font>
- **Purpose**: Scrapes public ladder matches, repackages into Parquet, and computes behavioral feature matrices.

| Script / Artifact  |          Implemented           |              Status               | Notes                                                                   |
| :----------------- | :----------------------------: | :-------------------------------: | :---------------------------------------------------------------------- |
| `data/scrape.py`   | <font color="green">Yes</font> | <font color="green">Active</font> | Scrapes episode replays from Kaggle's public episode API                |
| `data/repack.py`   | <font color="green">Yes</font> | <font color="green">Active</font> | Zstandard Parquet packaging (`replays.parquet`)                         |
| `data/teams.py`    | <font color="green">Yes</font> | <font color="green">Active</font> | Leaderboard team metadata sync (`teams.csv`)                            |
| `data/features.py` | <font color="green">Yes</font> | <font color="green">Active</font> | Extracts `episode_features.csv`, `stream_hashes.csv`, `daily_stats.csv` |

---

### Test Suite (`tests/`)

- **Status**: <font color="orange">Needs Overhaul (~30%)</font>
- **Purpose**: Unit and regression tests for planner, environment models, and action builders.

| Test File / Area        |             Implemented             |              Status              | Action Item                                                                                   |
| :---------------------- | :---------------------------------: | :------------------------------: | :-------------------------------------------------------------------------------------------- |
| `tests/test_planner.py` | <font color="orange">Partial</font> | <font color="red">Failing</font> | **TODO**: Fix legacy fixture invocation and update mock state schema to match `GameState`     |
| `tests/test_board.py`   |     <font color="red">No</font>     | <font color="red">Missing</font> | **TODO**: Unit tests for `Tile` getters, `Board` generators, and `nearest()` distance queries |
| `tests/test_economy.py` |     <font color="red">No</font>     | <font color="red">Missing</font> | **TODO**: Unit tests for crop ROI, profit, and threshold checks                               |
| `tests/test_market.py`  |     <font color="red">No</font>     | <font color="red">Missing</font> | **TODO**: Unit tests for price history, rolling trends, and `sell_score`                      |
| `tests/test_actions.py` |     <font color="red">No</font>     | <font color="red">Missing</font> | **TODO**: Unit tests for `ActionBuilder` factories and `merge()` logic                        |

---
