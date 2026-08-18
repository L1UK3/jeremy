from dataclasses import dataclass
from typing import Any

from actions import Action
from state import GameState


@dataclass(slots=True)
class Node:
    score: float
    action: Action
    state: GameState | None = None
    parent: Any = None


class Search:
    def __init__(self) -> None:
        self.nodes: list[Node] = []

    # --------------------------------------------------

    def clear(self) -> None:
        self.nodes.clear()

    # --------------------------------------------------

    def add(
        self,
        score: float,
        action: Action,
        state: GameState | None = None,
        parent: Any = None,
    ) -> None:

        self.nodes.append(
            Node(
                score=score,
                action=action,
                state=state,
                parent=parent,
            )
        )

    # --------------------------------------------------

    def empty(self) -> bool:
        return len(self.nodes) == 0

    # --------------------------------------------------

    def best(self) -> Node | None:
        if self.empty():
            return None
        return max(
            self.nodes,
            key=lambda n: n.score,
        )

    # --------------------------------------------------

    def topk(self, k: int = 5) -> list[Node]:
        return sorted(
            self.nodes,
            key=lambda n: n.score,
            reverse=True,
        )[:k]

    # --------------------------------------------------

    def choose(self) -> Action | None:
        node = self.best()
        if node is None:
            return None
        return node.action

    # --------------------------------------------------

    def dump(self) -> None:
        for n in self.topk():
            print(
                f"{n.score:8.2f}",
                n.action,
            )
