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

## Module: `agent.heuristics`

Subpackage containing modular decision evaluator functions that operate directly on a `Planner` instance, along with calibrated scoring constants.

### Module: `agent.heuristics.scores`
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

### Evaluator Functions
* **`evaluate_market(planner)`**: Evaluates farmhand hiring (`HIRE_HAND`), shed produce sales via `Market.best_item_to_sell()` (`SELL`), and seed purchases (`BUY_SEED`) using `planner.config.get_crop(planner.eco)`.
* **`evaluate_expansion(planner)`**: Evaluates quadrant land expansion (`BUY_LAND`) when financial buffer exceeds cost + \$300.
* **`evaluate_farming(planner)`**: Evaluates tile-level actions under the main farmer: harvest, weed clearing, watering, and planting.
* **`evaluate_movement(planner)`**: Evaluates directional movement toward nearest spatial targets.
* **`move_to(planner, tile) -> Action`**: Directional Manhattan navigation helper delegating to `Board.step_toward`.

---

## Module: `agent.jobs`

Composable task generation pipeline that populates the `Scheduler` with spatial jobs.

### Task Generators
* **`harvest_jobs(planner, crop: str) -> list[Job]`**: Yields harvest jobs for all ripe plants on the board. Score: $\text{HARVEST\_BASE} + (\text{yield} \times \text{price})$.
* **`water_jobs(planner, crop: str) -> list[Job]`**: Yields watering jobs for thirsty crops that are not yet ripe. Score: $\text{WATER}$.
* **`weed_jobs(planner, crop: str) -> list[Job]`**: Yields weeding jobs for obstacles on unlocked quadrants. Score: $\text{DIG\_WEED}$.
* **`plant_jobs(planner, crop: str) -> list[Job]`**: Yields planting jobs for empty unlocked tiles when seeds are in inventory. Score: $\text{PLANT\_BASE} + \text{ROI}$.

### Pipeline Assembly
* **`DEFAULT_JOB_PIPELINE: tuple`**: Default tuple of generators `(harvest_jobs, water_jobs, weed_jobs, plant_jobs)`.
* **`schedule_jobs(planner, target_crop: str | None = None, pipeline=DEFAULT_JOB_PIPELINE) -> None`**: Clears the scheduler, resolves active crop via `planner.config.get_crop(planner.eco)`, and populates the scheduler from the pipeline.

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
    item: str | None = None
```

### Pure Dispatch Helpers
* **`default_utility_scorer(job: Job, x: int, y: int, dist_penalty: float = 2.0) -> float`**:
  Calculates worker-specific utility: $\text{Utility} = \text{job.priority} - (\text{dist\_penalty} \times \text{distance})$.
* **`job_to_action(job: Job | None, x: int, y: int) -> Action`**:
  Translates a target job into a concrete action: emits the task action if standing on target `(x, y)`, or a single navigation step toward `job.target` via `step_toward`.

### `class Scheduler`
Multi-unit task allocation queue for assigning non-overlapping spatial tasks across the main farmer and hired farmhands.

```python
class Scheduler:
    def __init__(self, state: GameState) -> None: ...
```

#### Methods
* **`add_job(priority: float, action: str, target: tuple[int, int], item: str | None = None) -> None`**: Appends a job.
* **`extend_jobs(jobs: list[Job]) -> None`**: Batch appends a list of jobs.
* **`clear() -> None`**: Empties the job list.
* **`assign(scorer: Callable = default_utility_scorer) -> tuple[Action, list[Action]]`**:
  Dispatches optimal, non-overlapping tasks to the farmer and all hired farmhands. Returns `(farmer_action, [hand_action_1, hand_action_2, ...])`.

---

## Module: `agent.search`

### `class Node`
Container storing scored candidate actions.

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
   Calls `evaluate_market(self)` and `evaluate_expansion(self)` to generate scored market orders in `self.search`. Extracts merged market transactions via `self.choose()`.
2. **Stage 2 — Multi-Unit Job Scheduling**:
   Calls `schedule_jobs(self)` to populate `self.scheduler` with active farm tasks. Executes `self.scheduler.assign()` to dispatch non-overlapping actions to the farmer and all hired farmhands.
3. **Stage 3 — Action Synthesis**:
   Synthesizes and returns `Action(farmer=farmer_act, hands=hands_acts, market=market_action.market)`.

