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

**Maturation Horizon**:
The remaining season duration evaluated against a crop's growth curve to determine if planting will yield harvestable commodity before game termination.
_Avoid_: Crop timer, growth check, seed expiry

**Animal Structure**:
A specialized tile construction (`COOP` or `PASTURE`) deployed on reserved tiles to house specific livestock species (`GOOSE` or `COW`/`SHEEP`).
_Avoid_: Barn, pen, animal house

**Animal Plot Quota**:
The maximum number of animal structures assigned to each unlocked quadrant. Animal structures are distributed across unlocked quadrants by current structure count, with deterministic quadrant-order tie breaking.
_Avoid_: Species quota, livestock zone

**Labor Floor**:
The minimum deterministic count of hired farm hands required to maintain daily watering and planting chores across all unlocked quadrants before applying neural policy recommendations.
_Avoid_: Worker min, base crew, hand threshold

