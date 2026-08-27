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
    max_hires_per_day: int = 8
    expand_land: bool = True
    max_quadrants: int = 3
```

#### Properties & Methods
* `get_crop(eco: Economy) -> str | None` — Resolves the target crop dynamically using live ROI and end-game maturity horizon.
* `get_max_hires(state: GameState) -> int` — Dynamically scales the daily hiring limit based on in-game day (early vs peak vs end-game), unlocked quadrants, and available coin reserves.

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
* **`harvest_jobs(planner: Planner) -> list[Job]`**: Yields harvest jobs for all ripe plants and productive animals. Score: $\text{HARVEST\_BASE} + (\text{yield} \times \text{price})$.
* **`feed_jobs(planner: Planner) -> list[Job]`**: Yields feeding jobs for unfed animals when wheat is available in shed. Score: $\text{FEED\_URGENT}$ (if `consecutive_unfed >= 1`) or $\text{FEED}$.
* **`water_jobs(planner: Planner) -> list[Job]`**: Yields watering jobs for thirsty crops that are not yet ripe. Score: $\text{WATER}$.
* **`collect_fertilizer_jobs(planner: Planner) -> list[Job]`**: Yields fertilizer collection jobs on animal tiles with ready fertilizer. Score: $\text{COLLECT\_FERTILIZER}$.
* **`care_jobs(planner: Planner) -> list[Job]`**: Yields caring/petting jobs for animals not cared for today. Score: $\text{CARE}$.
* **`weed_jobs(planner: Planner) -> list[Job]`**: Yields weeding jobs for obstacles on unlocked quadrants. Score: $\text{DIG\_WEED}$.
* **`plant_jobs(planner: Planner, crop: str) -> list[Job]`**: Yields planting jobs for empty unlocked tiles when seeds are in inventory. Score: $\text{PLANT\_BASE} + \text{ROI}$.
* **`schedule_jobs(planner: Planner, target_crop: str | None = None) -> None`**: Helper populating `planner.scheduler` with all active spatial crop jobs.
* **`manage_livestock(planner: Planner, worker_idx: int = 0, worker_pos: tuple[int, int] | None = None) -> list[str] | None`**: High-priority morning chore state machine managing physical shed pickup of wheat, livestock feeding, petting/caring, byproduct harvesting, and depositing collected yield/fertilizer at the shed.

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
    def __init__(
        self, state: GameState, scorer: Callable = default_utility_scorer
    ) -> None: ...
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

## Module: `agent.opening`

### `OPENING_TRACE: dict[int, dict]`

Deterministic action trace covering initial turns (Days 1–2, turns 1–48) extracted from top-performing competitive replays to establish baseline animal husbandry, farmhand hiring, and crop rotation.

---

## Module: `agent.expanse`

### `EXPANSION_TRACE: dict[int, dict]`

Deterministic expansion action trace covering quadrant expansion milestones:
* **Day 8 (Steps 169–192)**: First expansion into Northeast quadrant (`NE`), building pastures, seeding strawberries, and placing sheep and cows.
* **Day 12 (Steps 265–288)**: Second expansion into Southwest quadrant (`SW`), building additional pastures, melon/strawberry crop planting, and managing a 14-worker crew.

---

## Module: `agent.planner`

### `class Planner`

Turn decision coordinator orchestrating opening/expansion execution, market evaluation, multi-unit scheduling, and action synthesis.

```python
class Planner:
    def __init__(
        self,
        state: GameState,
        config: AgentConfig | None = None,
    ) -> None: ...
```

#### Execution Loop (`Planner.play() -> Action`)

1. **Stage 1 — Deterministic Traces**:
   Checks `if step in OPENING_TRACE` or `if step in EXPANSION_TRACE` to execute optimal multi-unit trajectories for opening and land expansion.
2. **Stage 2 — Market & Strategy**:
   Evaluates market and expansion candidates via `evaluate_market` and `evaluate_expansion`, populating `self.search`. Extracts merged market transactions via `self.choose()`.
3. **Stage 3 — Multi-Unit Job Scheduling**:
   Calls `schedule_jobs(...)` to create active farm tasks and populates `self.scheduler`. Executes `self.scheduler.assign()` to dispatch non-overlapping actions to the farmer and all hired farmhands.
4. **Stage 4 — Action Synthesis**:
   Synthesizes and returns `Action(farmer=farmer_act, hands=hands_acts, market=market_action.market)`.



