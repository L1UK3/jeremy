# Reference: Agent API

This document provides the technical specification and API reference for the decision-making and planning modules in `src/agent/`.

---

## Module: `agent.config`

### `class AgentConfig`

Dataclass storing high-level policy constants and hyperparameters controlling agent behavior.

```python
@dataclass(slots=True)
class AgentConfig:
    target_crop: str = "MELON"
    sell_threshold: int = 200
    seed_target: int = 1
    expand_land: bool = False
    max_hires_per_day: int = 0
```

#### Properties
* `seed_cost: int` — Looked up from `CROPS[target_crop]["seed"]`.
* `max_yield_day: int` — Looked up from `CROPS[target_crop]["max_yield_day"]`.

#### Global Instance
* `DEFAULT_CONFIG: AgentConfig` — Default configuration initialized with standard single-crop maximizing defaults.

---

## Module: `agent.heuristics`

Subpackage containing modular decision evaluator functions that operate directly on a `Planner` instance, along with calibrated scoring constants.

### Module: `agent.heuristics.scores`
Utility score constants adhering to the Score Calibration Hierarchy:
* `SCORE_HARVEST_BASE: float = 100.0`
* `SCORE_BUY_LAND: float = 100.0`
* `SCORE_DIG_WEED: float = 90.0`
* `SCORE_WATER: float = 80.0`
* `SCORE_PLANT_BASE: float = 60.0`
* `SCORE_SELL: float = 50.0`
* `SCORE_BUY_SEED: float = 40.0`
* `SCORE_MOVE_HARVEST: float = 40.0`
* `SCORE_MOVE_WATER: float = 30.0`
* `SCORE_MOVE_EMPTY: float = 20.0`

### Evaluator Functions
* **`evaluate_market(planner)`**: Evaluates seed purchasing (`SCORE_BUY_SEED`) and produce selling (`SCORE_SELL`) against config thresholds.
* **`evaluate_farming(planner)`**: Evaluates tile-level actions: harvest (`SCORE_HARVEST_BASE + value`), weed clearing (`SCORE_DIG_WEED`), watering (`SCORE_WATER`), and planting (`SCORE_PLANT_BASE + ROI`).
* **`evaluate_movement(planner)`**: Evaluates directional movement toward nearest harvestable (`SCORE_MOVE_HARVEST`), thirsty (`SCORE_MOVE_WATER`), or empty soil (`SCORE_MOVE_EMPTY`) targets.
* **`evaluate_expansion(planner)`**: Evaluates land expansion (`SCORE_BUY_LAND`).
* **`move_to(planner, tile) -> Action`**: Directional Manhattan navigation helper.

---

## Module: `agent.planner`

### `class Planner`

Main planning coordinator that holds turn state and coordinates the evaluator functions.

```python
class Planner:
    def __init__(
        self,
        state: GameState,
        config: AgentConfig | None = None,
    ) -> None: ...
```

#### Instance Attributes
* `state: GameState` — Current turn game state wrapper.
* `config: AgentConfig` — Active agent configuration (defaults to `DEFAULT_CONFIG`).
* `board: Board` — Spatial grid manager.
* `eco: Economy` — ROI and cost calculator.
* `search: Search` — Priority candidate action queue.
* `heuristics: list[Heuristic]` — Ordered evaluation pipeline (defaults to `DEFAULT_HEURISTICS`).

#### Methods

##### `add(score: float, action: Action) -> None`
Pushes a candidate action with an assigned numerical utility score to `self.search`.

##### `evaluate_market() -> None`
Delegates to `MarketHeuristic().evaluate(...)`.

##### `evaluate_current_tile() -> None`
Delegates to `FarmingHeuristic().evaluate(...)`.

##### `evaluate_movement() -> None`
Delegates to `MovementHeuristic().evaluate(...)`.

##### `evaluate_expansion() -> None`
Delegates to `ExpansionHeuristic().evaluate(...)`.

##### `move_to(tile: Tile) -> Action`
Computes a single Manhattan step (`NORTH`, `SOUTH`, `EAST`, or `WEST`) from farmer position `(fx, fy)` toward `(tile.x, tile.y)`. Returns `ActionBuilder.pass_turn()` if already at destination.

##### `choose() -> Action`
Merges all candidate nodes in `self.search` using `ActionBuilder.merge()`.

##### `play() -> Action`
Iterates through `self.heuristics`, evaluates candidate actions into `self.search`, and returns the merged `Action`.

---

## Module: `agent.search`

### `class Node`
A lightweight dataclass container storing scored candidate actions.

```python
@dataclass(slots=True)
class Node:
    score: float
    action: Action
    state: GameState | None = None
    parent: Any = None
```

---

### `class Search`
Priority candidate pool for accumulating, sorting, and pruning candidate actions.

```python
class Search:
    def __init__(self) -> None: ...
```

#### Methods

##### `clear() -> None`
Clears all registered nodes.

##### `add(score: float, action: Action, state: GameState | None = None, parent: Any = None) -> None`
Appends a new `Node` to `self.nodes`.

##### `empty() -> bool`
Returns `True` if `len(self.nodes) == 0`.

##### `best() -> Node | None`
Returns the node with maximum `score`, or `None` if empty.

##### `topk(k: int = 5) -> list[Node]`
Returns the top `k` nodes sorted in descending order by `score`.

##### `choose() -> Action | None`
Returns `best().action` or `None` if empty.

##### `dump() -> None`
Prints the top-5 scored actions to stdout for debugging.

---

## Module: `agent.scheduler`

### `class Job`
Dataclass representing a unit task assignment for multi-agent coordination.

```python
@dataclass(slots=True)
class Job:
    priority: float
    action: str
    target: tuple[int, int]
    actor: str = "farmer"
```

---

### `class Scheduler`
Multi-unit task allocation queue for assigning non-overlapping spatial tasks across the main farmer and hired farmhands.

```python
class Scheduler:
    def __init__(self, state: GameState) -> None: ...
```

#### Methods

##### `add_job(action: str, x: int, y: int, priority: float, actor: str = "farmer") -> None`
Adds a new job target to `self.jobs`.

##### `sort() -> None`
Sorts `self.jobs` in-place in descending order of `priority`.

##### `best() -> Job | None`
Returns the highest-priority job.

##### `assign() -> tuple[Job | None, list[Job]]`
Greedily dispatches jobs to units while ensuring no two units target the same `(x, y)` coordinate. Returns `(farmer_job, [hand_job_1, hand_job_2, ...])`.

##### `clear() -> None`
Empties the job queue.
