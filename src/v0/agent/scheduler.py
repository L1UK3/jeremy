from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING

from src.v0.environment.board import step_toward

if TYPE_CHECKING:
    from src.v0.environment.state import GameState

__all__ = ["Job", "Scheduler", "default_utility_scorer", "job_to_action"]


@dataclass(slots=True)
class Job:
    priority: float
    action: str
    target: tuple[int, int]
    actor: str = "farmer"
    item: str | None = None


def default_utility_scorer(
    job: Job, x: int, y: int, dist_penalty: float = 2.0
) -> float:
    """Distance-discounted utility from an actor position (x, y)."""
    return job.priority - (
        dist_penalty * (abs(x - job.target[0]) + abs(y - job.target[1]))
    )


def job_to_action(job: Job, x: int, y: int) -> list[str]:
    """Convert a job into a movement step or tile action for actor at (x, y)."""
    tx, ty = job.target
    if (x, y) == (tx, ty):
        act = job.action
        if act == "PLANT":
            return ["PLANT", job.item] if job.item else ["PLANT"]
        if act == "HARVEST":
            return ["HARVEST"]
        if act == "WATER":
            return ["WATER"]
        if act == "DIG":
            return ["DIG"]
        if act == "FEED":
            return ["FEED"]
        if act == "CARE":
            return ["CARE"]
        if act == "COLLECT_FERTILIZER":
            return ["COLLECT_FERTILIZER"]
        if act == "FERTILIZE":
            return ["FERTILIZE"]
        return [act]

    step = step_toward(x, y, tx, ty)
    return [step] if step != "PASS" else ["PASS"]


class Scheduler:
    def __init__(
        self,
        state: GameState,
        scorer: Callable[[Job, int, int], float] = default_utility_scorer,
    ) -> None:
        self.state = state
        self.jobs: list[Job] = []
        self.scorer = scorer

    def add_job(
        self,
        action: str,
        x: int,
        y: int,
        priority: float,
        actor: str = "farmer",
        item: str | None = None,
    ) -> None:
        self.jobs.append(
            Job(
                priority=priority,
                action=action,
                target=(x, y),
                actor=actor,
                item=item,
            )
        )

    def extend_jobs(self, jobs: Sequence[Job]) -> None:
        self.jobs.extend(jobs)

    def _assign_one(
        self, x: int, y: int, used: set[tuple[int, int]]
    ) -> list[str]:
        if self.scorer is default_utility_scorer:
            best_job = None
            best_score = -1e9
            for j in self.jobs:
                if j.target not in used:
                    score = j.priority - 2.0 * (
                        abs(x - j.target[0]) + abs(y - j.target[1])
                    )
                    if score > best_score:
                        best_score = score
                        best_job = j
            if best_job is not None:
                used.add(best_job.target)
                return job_to_action(best_job, x, y)
            return ["PASS"]

        available = (j for j in self.jobs if j.target not in used)
        if best := max(
            available, key=lambda j: self.scorer(j, x, y), default=None
        ):
            used.add(best.target)
            return job_to_action(best, x, y)
        return ["PASS"]

    def assign(self) -> tuple[list[str], list[list[str]]]:
        farmer_pos = self.state.farmer
        hands = self.state.hands
        used: set[tuple[int, int]] = set()

        farmer_act = self._assign_one(farmer_pos[0], farmer_pos[1], used)
        hands_acts = [self._assign_one(h[0], h[1], used) for h in hands]
        return farmer_act, hands_acts

    def clear(self) -> None:
        self.jobs.clear()
