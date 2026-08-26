# Reference: Agent API

This document provides the technical specification and API reference for the decision-making and planning modules in `src/agent/`.

---

## Module: `agent.config`

### `class AgentConfig`

Dataclass storing high-level policy constants and hyperparameters controlling agent behavior.

```python
@dataclass(slots=True)
class AgentConfig:
    target_crop: str = "WHEAT"
    sell_threshold: int = 180
    seed_target: int = 12
    expand_land: bool = True
    max_hires_per_day: int = 3
    dynamic_crops: bool = True
    max_quadrants: int = 2
```

#### Properties & Methods
* `seed_cost: int` — Looked up from `CROPS[target_crop]["seed"]`.
* `max_yield_day: int` — Looked up from `CROPS[target_crop]["max_yield_day"]`.
* `get_crop(eco: Economy) -> str` — Resolves the target crop dynamically using live ROI and end-game maturity horizon if `dynamic_crops` is enabled; otherwise returns `self.target_crop`.

#### Global Instance
* `DEFAULT_CONFIG: AgentConfig` — Default configuration initialized with standard production defaults.

---

## Module: `agent.scores`

Utility score constants adhering to the Score Calibration Hierarchy:

```python
# Tier 1: Immediate Revenue & Crop Preservation
HARVEST_BASE: float = 150.0
WATER: float = 120.0

# Tier 2: Essential Inputs & Multipliers
BUY_SEED: float = 100.0
HIRE_HAND: float = 95.0
SELL: float = 90.0

# Tier 3: Farm Expansion & Seeding
BUY_LAND: float = 85.0
PLANT_BASE: float = 75.0
DIG_WEED: float = 60.0
FERTILIZER: float = 50.0

# Tier 4: Single-unit Movement Fallbacks
MOVE_HARVEST: float = 40.0
MOVE_WATER: float = 35.0
MOVE_WEED: float = 30.0
MOVE_EMPTY: float = 20.0
```

---

## Module: `agent.evaluators`

Pure decision evaluator functions that inspect environment state models and return scored candidate actions:

* **`evaluate_market(state: GameState, eco: Economy, market: Market, board: Board, config: AgentConfig) -> list[tuple[float, Action]]`**:
  Evaluates farmhand hiring (`HIRE_HAND`), produce sales via `Market.best_item_to_sell()` (`SELL`), and seed purchases (`BUY_SEED`) based on active crop.
* **`evaluate_expansion(state: GameState, eco: Economy, config: AgentConfig) -> tuple[float, Action] | None`**:
  Evaluates purchasing adjacent land quadrants (`BUY_LAND`) when financial threshold is satisfied.


---

## Module: `agent.jobs`

Pure task generation pipeline that populates the `Scheduler` with spatial jobs.

### Task Generators
* **`harvest_jobs(board: Board, eco: Economy, day: int, crop: str) -> list[Job]`**: Yields harvest jobs for all ripe plants on the board. Score: $\text{HARVEST\_BASE} + (\text{yield} \times \text{price})$.
* **`water_jobs(board: Board, crop: str) -> list[Job]`**: Yields watering jobs for thirsty crops that are not yet ripe. Score: $\text{WATER}$.
* **`weed_jobs(board: Board) -> list[Job]`**: Yields weeding jobs for obstacles on unlocked quadrants. Score: $\text{DIG\_WEED}$.
* **`plant_jobs(board: Board, eco: Economy, state: GameState, crop: str) -> list[Job]`**: Yields planting jobs for empty unlocked tiles when seeds are in inventory. Score: $\text{PLANT\_BASE} + \text{ROI}$.

### Pipeline Assembly
* **`generate_jobs(board: Board, eco: Economy, state: GameState, config: AgentConfig, target_crop: str | None = None) -> list[Job]`**: Generates the complete list of spatial farm jobs across all categories.
* **`schedule_jobs(planner, target_crop: str | None = None, pipeline=DEFAULT_JOB_PIPELINE) -> None`**: Helper populating `planner.scheduler` from `generate_jobs`.

---

## Module: `agent.scheduler`

### `class Job`
Pure dataclass representing a discrete spatial task for multi-agent dispatching.

```python
@dataclass(slots=True)
class Job:
    priority: float
    action: str
    target: tuple[int, int]
    actor: str = "farmer"
    item: str | None = None
```

### Pure Dispatch Helpers
* **`default_utility_scorer(job: Job, x: int, y: int, dist_penalty: float = 2.0) -> float`**:
  Calculates worker-specific utility: $\text{Utility} = \text{job.priority} - (\text{dist\_penalty} \times \text{distance})$.
* **`job_to_action(job: Job, x: int, y: int) -> list[str]`**:
  Translates a target job into a concrete action for actor at `(x, y)`: emits the task action if standing on `job.target`, or a navigation step toward `job.target`.

### `class Scheduler`
Multi-unit task allocation queue for assigning non-overlapping spatial tasks across the main farmer and hired farmhands.

```python
class Scheduler:
    def __init__(self, state: GameState, scorer: Callable = default_utility_scorer) -> None: ...
```

#### Methods
* **`add_job(action: str, x: int, y: int, priority: float, actor: str = "farmer", item: str | None = None) -> None`**: Appends a job.
* **`extend_jobs(jobs: Sequence[Job]) -> None`**: Batch appends a sequence of jobs.
* **`clear() -> None`**: Empties the job list.
* **`assign() -> tuple[list[str], list[list[str]]]`**:
  Dispatches optimal, non-overlapping tasks to the farmer and all hired farmhands. Returns `(farmer_action, [hand_action_1, hand_action_2, ...])`.

---

## Module: `agent.search`

### `class Node`
Container storing candidate actions with priority scoring and optional state/parent references for search trees.

```python
@dataclass(slots=True)
class Node:
    score: float
    action: Action
    state: GameState | None = None
    parent: Any = None
```

### `class Search`
Priority candidate pool for accumulating, sorting, and pruning candidate actions.

```python
class Search:
    def __init__(self) -> None: ...
```

#### Methods
* **`clear() -> None`**: Clears all registered nodes.
* **`add(score: float, action: Action, state: GameState | None = None, parent: Any = None) -> None`**: Appends a new `Node`.
* **`empty() -> bool`**: Returns `True` if `len(self.nodes) == 0`.
* **`best() -> Node | None`**: Returns the node with maximum `score`.
* **`topk(k: int = 5) -> list[Node]`**: Returns top $k$ nodes sorted in descending order by `score`.
* **`choose() -> Action | None`**: Returns the action of the highest scoring node.

---

## Module: `agent.planner`

### `class Planner`

Turn decision coordinator orchestrating market evaluation, multi-unit scheduling, and action synthesis.

```python
class Planner:
    def __init__(
        self,
        state: GameState,
        config: AgentConfig | None = None,
    ) -> None: ...
```

#### Execution Loop (`Planner.play() -> Action`)

1. **Stage 1 — Market & Strategy**:
   Evaluates market and expansion candidates via `evaluate_market` and `evaluate_expansion`, populating `self.search`. Extracts merged market transactions via `self.choose()`.
2. **Stage 2 — Multi-Unit Job Scheduling**:
   Calls `generate_jobs(...)` to create active farm tasks and populates `self.scheduler`. Executes `self.scheduler.assign()` to dispatch non-overlapping actions to the farmer and all hired farmhands.
3. **Stage 3 — Action Synthesis**:
   Synthesizes and returns `Action(farmer=farmer_act, hands=hands_acts, market=market_action.market)`.


