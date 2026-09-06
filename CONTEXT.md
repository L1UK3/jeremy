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

