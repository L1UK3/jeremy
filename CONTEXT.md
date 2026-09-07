# Jeremy Agent Context

The competitive Kaggriculture agent architecture, defining strategic economic planning and spatial multi-agent coordination.

## Language

**Macro Policy**:
A neural network policy evaluated once per day that dictates high-level economic intent: target crop, target livestock, crew size, market reservation price scales, and predation posture.
_Avoid_: Micro policy, trace, heuristic planner

**Spatial Dispatcher**:
The centralized multi-agent coordinator that computes distance-discounted utility over candidate field jobs and assigns non-overlapping turn actions across all units.
_Avoid_: Job queue, worker thread, path trace

**Chore Job**:
A prioritized spatial task specification `(priority, action, target_tile, item)` evaluated against unit distance to score utility.
_Avoid_: Task, order, ticket

**Center Drop**:
The four center tiles `(4,4), (5,4), (4,5), (5,5)` adjacent to the farm shed where units deposit backpack items via the `DROP` action.
_Avoid_: Barn, storage drop, home base

**Farm Hand**:
A temporary worker unit hired on a daily escalating Fibonacci cost curve to execute chores alongside the main farmer.
_Avoid_: Worker, clone, minion

**Supply Projection**:
An analytical estimation of remaining commodity yield across the season computed dynamically from game parameters, active assets, and unlocked quadrants.
_Avoid_: Static supply, supply trace, supply JSON

**Episode Invariant**:
A behavioral assertion evaluated against game step observations and actions from a live headless simulation or replay file to verify strategic correctness.
_Avoid_: Post-mortem check, log audit, replay inspection script

**Land Expansion**:
The unlocking of additional farm quadrants (`NE`, `SW`, `SE`) via `BUY_LAND` at verified capital and timing thresholds.
_Avoid_: Buying land turn, map expansion, territory buy

**Replay Provider**:
An abstraction supplying game steps for testing, dynamically resolving to either an in-memory headless episode execution or a pre-recorded replay file.
_Avoid_: Hardcoded replay, html parser, trace scraper

**Runtime Parameters**:
The frozen schema of subsystem configurations and default weights in `src/parameters.py` parsed by the agent at game start.
_Avoid_: Tuning knobs, trial config, search space

**Tuning Search Space**:
The optimization domain, distribution bounds, and trial sampling routines in `simulation/tuning/` explored by Optuna.
_Avoid_: Model parameters, hardcoded hyperparams, trial dataclass

