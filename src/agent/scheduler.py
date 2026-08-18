from dataclasses import dataclass


@dataclass(slots=True)
class Job:
    priority: float
    action: str
    target: tuple
    actor: str = "farmer"


class Scheduler:
    def __init__(self, state):
        self.state = state
        self.jobs = []

    # ----------------------------------------------------

    def add_job(self, action: str, x: int, y: int, priority: float, actor: str = "farmer") -> None:
        self.jobs.append(
            Job(
                priority=priority,
                action=action,
                target=(x, y),
                actor=actor,
            )
        )

    # ----------------------------------------------------

    def sort(self) -> None:
        self.jobs.sort(
            key=lambda j: j.priority,
            reverse=True,
        )

    # ----------------------------------------------------

    def best(self) -> Job | None:
        if not self.jobs:
            return None
        self.sort()
        return self.jobs[0]

    # ----------------------------------------------------

    def assign(self) -> tuple[Job | None, list[Job]]:
        self.sort()
        farmer = None
        hands = []
        used = set()
        for job in self.jobs:
            if job.target in used:
                continue
            used.add(job.target)
            if farmer is None:
                farmer = job
            else:
                hands.append(job)
        return farmer, hands

    # ----------------------------------------------------

    def clear(self) -> None:
        self.jobs.clear()
