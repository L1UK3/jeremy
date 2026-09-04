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

- `get_crop(eco: Economy) -> str | None` — Resolves the target crop dynamically using live ROI and end-game maturity horizon.
- `get_max_hires(state: GameState) -> int` — Dynamically scales the daily hiring limit based on in-game day (early vs peak vs end-game), unlocked quadrants, and available coin reserves.

#### Global Instance

- `DEFAULT_CONFIG: AgentConfig` — Default configuration initialized with standard production defaults.

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

- **`evaluate_market(state: GameState, eco: Economy, market: Market, board: Board, config: AgentConfig) -> list[tuple[float, Action]]`**:
  Evaluates farmhand hiring (`HIRE_HAND`), produce sales via `Market.best_item_to_sell()` (`SELL`), and seed purchases (`BUY_SEED`) based on active crop.
- **`evaluate_expansion(state: GameState, eco: Economy, config: AgentConfig) -> tuple[float, Action] | None`**:
  Evaluates purchasing adjacent land quadrants (`BUY_LAND`) when financial threshold is satisfied.

---

## Module: `agent.jobs`

Pure task generation pipeline that populates the `Scheduler` with spatial jobs.

### Task Generators

- **`harvest_jobs(planner: Planner) -> list[Job]`**: Yields harvest jobs for all ripe plants and productive animals. Score: $\text{HARVEST\_BASE} + (\text{yield} \times \text{price})$.
- **`feed_jobs(planner: Planner) -> list[Job]`**: Yields feeding jobs for unfed animals when wheat is available in shed. Score: $\text{FEED\_URGENT}$ (if `consecutive_unfed >= 1`) or $\text{FEED}$.
- **`water_jobs(planner: Planner) -> list[Job]`**: Yields watering jobs for thirsty crops that are not yet ripe. Score: $\text{WATER}$.
- **`collect_fertilizer_jobs(planner: Planner) -> list[Job]`**: Yields fertilizer collection jobs on animal tiles with ready fertilizer. Score: $\text{COLLECT\_FERTILIZER}$.
- **`care_jobs(planner: Planner) -> list[Job]`**: Yields caring/petting jobs for animals not cared for today. Score: $\text{CARE}$.
- **`weed_jobs(planner: Planner) -> list[Job]`**: Yields weeding jobs for obstacles on unlocked quadrants. Score: $\text{DIG\_WEED}$.
- **`plant_jobs(planner: Planner, crop: str) -> list[Job]`**: Yields planting jobs for empty unlocked tiles when seeds are in inventory. Score: $\text{PLANT\_BASE} + \text{ROI}$.
- **`schedule_jobs(planner: Planner, target_crop: str | None = None) -> None`**: Helper populating `planner.scheduler` with all active spatial crop jobs.
- **`manage_livestock(planner: Planner, worker_idx: int = 0, worker_pos: tuple[int, int] | None = None) -> list[str] | None`**: High-priority morning chore state machine managing physical shed pickup of wheat, livestock feeding, petting/caring, byproduct harvesting, and depositing collected yield/fertilizer at the shed.

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

- **`default_utility_scorer(job: Job, x: int, y: int, dist_penalty: float = 2.0) -> float`**:
  Calculates worker-specific utility: $\text{Utility} = \text{job.priority} - (\text{dist\_penalty} \times \text{distance})$.
- **`job_to_action(job: Job, x: int, y: int) -> list[str]`**:
  Translates a target job into a concrete action for actor at `(x, y)`: emits the task action if standing on `job.target`, or a navigation step toward `job.target`.

### Functional Task Dispatch Pipeline

- **`generate_jobs(state: GameState, board: Board, target_crop: str | None = None) -> list[Job]`**:
  Generates a list of spatial chores and farming jobs sorted by dynamic priority.
- **`assign_jobs(state: GameState, jobs: list[Job]) -> tuple[list[str], list[list[str]]]`**:
  Dispatches optimal, non-overlapping tasks to the farmer and all hired farmhands. Returns `(farmer_action, [hand_action_1, hand_action_2, ...])`.
- **`schedule_tasks(state: GameState, board: Board, target_crop: str | None = None) -> tuple[list[str], list[list[str]]]`**:
  Top-level scheduler pipeline generating prioritized chores and assigning tasks to units in a single call.

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

- **`clear() -> None`**: Clears all registered nodes.
- **`add(score: float, action: Action, state: GameState | None = None, parent: Any = None) -> None`**: Appends a new `Node`.
- **`empty() -> bool`**: Returns `True` if `len(self.nodes) == 0`.
- **`best() -> Node | None`**: Returns the node with maximum `score`.
- **`topk(k: int = 5) -> list[Node]`**: Returns top $k$ nodes sorted in descending order by `score`.
- **`choose() -> Action | None`**: Returns the action of the highest scoring node.

---

## Trajectories: `routes.json`

### `ROUTES: dict[int, dict]`

Deterministic action traces extracted from top-performing competitive replays (e.g. replay `90650891`):

- **Day 1 (Turns 0–23)**: Baseline animal husbandry, farmhand hiring, and crop rotation opening.
- **Day 8 (Steps 169–192)**: First expansion into Northeast quadrant (`NE`), building pastures, seeding strawberries, and placing sheep and cows.
- **Day 12 (Steps 265–288)**: Second expansion into Southwest quadrant (`SW`), building additional pastures, melon/strawberry crop planting, and managing a 14-worker crew.

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
   Checks `if step in ROUTES` to execute optimal multi-unit trajectories for opening and land expansion.
2. **Stage 2 — Market & Strategy**:
   Evaluates market and expansion candidates via `evaluate_market` and `evaluate_expansion`, populating `self.search`. Extracts merged market transactions via `self.choose()`.
3. **Stage 3 — Multi-Unit Job Scheduling**:
   Calls `schedule_jobs(...)` to create active farm tasks and populates `self.scheduler`. Executes `self.scheduler.assign()` to dispatch non-overlapping actions to the farmer and all hired farmhands.
4. **Stage 4 — Action Synthesis**:
   Synthesizes and returns `Action(farmer=farmer_act, hands=hands_acts, market=market_action.market)`.

---

## Module: `agent.explosion`

### `explosion(planner: Planner) -> Action`

Final 8-turn liquidation controller (turns 712–719, Day 30 hours 16–23).
Maximizes final coin balance before step 720 game termination through coordinated harvest routes, shed deposits, and aggressive glut-weighted market liquidations:

1. **Same-Turn Shed Deposit Projections**: Identifies all workers executing `DROP` at shed-adjacent tiles on the current turn, adding their carried goods into projected shed stock for same-turn market liquidation.
2. **Glut-Weighted Market Liquidation**: Liquidates all available produce across 9 sellable goods (`MELON`, `WOOL`, `MILK`, `STRAWBERRY`, `EGG`, `TOMATO`, `CARROT`, `WHEAT`, `FERTILIZER`) ordered by market impact and value.
3. **Reachability-Bounded Worker Routing**: Validates complete round-trips ($\text{dist}(worker, crop) + \text{harvest} + \text{dist}(crop, shed) + \text{drop} \le \text{turns\_left}$) before assigning harvest tasks, with urgent shed-return overrides when carrying inventory near match end.

---

## Module: `src/main.py` (Phase Sub-Agents & Wrapper)

`src/main.py` provides the top-level callback `agent(obs)` that delegates execution across four specialized phase sub-agents:

### `opening_agent(obs: dict[str, Any], state: GameState | None = None) -> dict[str, Any]`
Executes high-yield scripted opening traces (turns 0–23 / Day 1) from `ROUTES` to establish animal husbandry, initial crops, and early worker hires. Gracefully falls back to `main_agent` if unscripted.

### `expansion_agent(obs: dict[str, Any], state: GameState | None = None) -> dict[str, Any]`
Executes quadrant expansion trajectories (e.g. Northeast expansion at turns 169–192, Southwest expansion at turns 265–288) from `ROUTES`. Gracefully falls back to `main_agent` if unscripted.

### `explosion_agent(obs: dict[str, Any], state: GameState | None = None, board: Board | None = None) -> dict[str, Any]`
Executes the final 8-turn endgame liquidation controller (`explosion(state, board)` for turns 712–719).

### `main_agent(obs: dict[str, Any], state: GameState | None = None, board: Board | None = None, eco: Economy | None = None, market: Market | None = None, scheduler: Scheduler | None = None) -> dict[str, Any]`
Handles dynamic mid-game agricultural operations: market order evaluation (`evaluate_market`), expansion triggering (`evaluate_expansion`), livestock care (`evaluate_livestock`), crop task population, and worker assignment (`Scheduler.assign`).

### `agent(obs: dict[str, Any]) -> dict[str, Any]`
Main environment entrypoint wrapper routing each turn based on step index:
- `step < 24` $\to$ `opening_agent`
- `step >= 712` $\to$ `explosion_agent`
- `step in ROUTES` (turns 169–192, 265–288) $\to$ `expansion_agent`
- Otherwise $\to$ `main_agent`

