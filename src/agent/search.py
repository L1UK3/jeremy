from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from environment.actions import Action

__all__ = ["Node", "Search"]


@dataclass(slots=True)
class Node:
    score: float
    action: Action


class Search:
    """Candidate action pool for evaluating and ranking candidate moves and market orders."""

    def __init__(self) -> None:
        self.nodes: list[Node] = []

    def clear(self) -> None:
        self.nodes.clear()

    def add(self, score: float, action: Action) -> None:
        self.nodes.append(Node(score=score, action=action))

    def empty(self) -> bool:
        return len(self.nodes) == 0

    def best(self) -> Node | None:
        if not self.nodes:
            return None
        return max(self.nodes, key=lambda n: n.score)

    def topk(self, k: int = 5) -> list[Node]:
        return sorted(self.nodes, key=lambda n: n.score, reverse=True)[:k]

    def choose(self) -> Action | None:
        node = self.best()
        return node.action if node is not None else None
