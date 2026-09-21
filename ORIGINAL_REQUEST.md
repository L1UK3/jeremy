# Original User Request

## 2026-09-21T19:37:09Z

Implement all 11 open issues in `.scratch/` across 3 dedicated git feature branches (`feature/animal-plot-placement`, `feature/farmer-inactivity-diagnosis`, `feature/fix-weed-and-100k-invariants`), verify with automated tests, and merge each into `main`.

Working directory: `d:\Projects\jeremy`
Integrity mode: development

## Requirements

### R1. Animal Plot Placement (`feature/animal-plot-placement`)
Implement the 3 issues in `.scratch/animal-plot-placement/issues/`:
- Center-symmetric animal plot reflection across quadrant boundaries.
- Capped animal plot reservations per quadrant.
- Fallback candidate selection when plots are crop-occupied.

### R2. Farmer Inactivity Diagnosis (`feature/farmer-inactivity-diagnosis`)
Implement the 4 issues in `.scratch/farmer-inactivity-diagnosis/issues/`:
- Make silent farmer exceptions visible during simulation execution.
- Allocate farmer priority chores over passive waiting.
- Reposition idle farmers toward center drop or pending chores.
- Enforce farmer liveness episode invariants.

### R3. Weed and 100k Invariants (`feature/fix-weed-and-100k-invariants`)
Implement the 4 issues in `.scratch/fix-weed-and-100k-invariants/issues/`:
- Accelerated melon capital liquidation logic.
- Post-melon livestock scaling.
- Early strawberry carpet saturation.
- 100k benchmark integration suite.

### R4. Git Feature Branching & Clean Merges
- For each feature, create a dedicated branch (`feature/<feature-name>`).
- Implement the tickets, commit progress with clear commit messages.
- Verify tests pass on the branch, then merge into `main` sequentially, resolving any conflicts.

## Verification Resources
- Test suite: `pytest tests/`
- Linter: `ruff check .`
- Issue specifications: `.scratch/<feature>/spec.md` and `.scratch/<feature>/issues/*.md`

## Acceptance Criteria

### Branch & Merge Integrity
- [ ] 3 feature branches (`feature/animal-plot-placement`, `feature/farmer-inactivity-diagnosis`, `feature/fix-weed-and-100k-invariants`) created, committed, and merged into `main`.
- [ ] `git status` on `main` is clean after final merge.

### Functionality & Tests
- [ ] `pytest tests/` runs and passes with 0 failures on `main`.
- [ ] `ruff check .` passes with 0 errors.

### Issue Tracker Completion
- [ ] All 11 ticket files in `.scratch/` have all checklist items marked complete (`[x]`).
- [ ] Status line in each of the 11 ticket files is updated to `resolved`.
