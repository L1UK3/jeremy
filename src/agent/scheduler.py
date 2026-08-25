from collections.abc import Callable
from dataclasses import dataclass

from environment.actions import ActionBuilder
from environment.board import manhattan_distance, step_toward


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
        dist_penalty * manhattan_distance(x, y, job.target[0], job.target[1])
    )


def job_to_action(job: Job, x: int, y: int) -> list[str]:
    """Convert a job into a movement step or tile action for actor at (x, y)."""
    if (x, y) == job.target:
        if job.action == "PLANT":
            return (
                ActionBuilder.plant(job.item).farmer if job.item else ["PLANT"]
            )
        if job.action == "HARVEST":
            return ActionBuilder.harvest().farmer
        if job.action == "WATER":
            return ActionBuilder.water().farmer
        if job.action == "DIG":
            return ActionBuilder.dig().farmer
        if job.action == "FERTILIZE":
            return ActionBuilder.fertilize().farmer
        return [job.action]

    step = step_toward(x, y, job.target[0], job.target[1])
    return (
        ActionBuilder.move(step).farmer
        if step != "PASS"
        else ActionBuilder.pass_turn().farmer
    )


class Scheduler:
    def __init__(
        self,
        state,
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

    def extend_jobs(self, jobs: list[Job]) -> None:
        self.jobs.extend(jobs)

    def _assign_one(
        self, x: int, y: int, used: set[tuple[int, int]]
    ) -> list[str]:
        available = (j for j in self.jobs if j.target not in used)
        if best := max(
            available, key=lambda j: self.scorer(j, x, y), default=None
        ):
            used.add(best.target)
            return job_to_action(best, x, y)
        return ActionBuilder.pass_turn().farmer

    def assign(self) -> tuple[list[str], list[list[str]]]:
        actors = [self.state.farmer, *(tuple(h) for h in self.state.hands)]
        used: set[tuple[int, int]] = set()
        actions = [self._assign_one(x, y, used) for x, y in actors]
        return actions[0], actions[1:]

    def clear(self) -> None:
        self.jobs.clear()
