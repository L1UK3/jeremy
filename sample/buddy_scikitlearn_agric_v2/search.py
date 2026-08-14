from dataclasses import dataclass


@dataclass(slots=True)
class Node:

    score: float

    action: object

    state=None

    parent=None


class Search:

    def __init__(self):

        self.nodes = []

    # --------------------------------------------------

    def clear(self):

        self.nodes.clear()

    # --------------------------------------------------

    def add(

        self,

        score,

        action,

        state=None,

        parent=None,

    ):

        self.nodes.append(

            Node(

                score=score,

                action=action,

                state=state,

                parent=parent,

            )

        )

    # --------------------------------------------------

    def empty(self):

        return len(self.nodes) == 0

    # --------------------------------------------------

    def best(self):

        if self.empty():

            return None

        return max(

            self.nodes,

            key=lambda n: n.score,

        )

    # --------------------------------------------------

    def topk(self, k=5):

        return sorted(

            self.nodes,

            key=lambda n: n.score,

            reverse=True,

        )[:k]

    # --------------------------------------------------

    def choose(self):

        node = self.best()

        if node is None:

            return None

        return node.action

    # --------------------------------------------------

    def dump(self):

        for n in self.topk():

            print(

                f"{n.score:8.2f}",

                n.action,

            )
