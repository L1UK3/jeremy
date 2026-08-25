from agent.config import DEFAULT_CONFIG, AgentConfig
from agent.heuristics import (
    evaluate_expansion,
    evaluate_farming,
    evaluate_market,
    evaluate_movement,
    move_to,
)
from agent.scheduler import Scheduler
from agent.search import Search
from environment.actions import Action, ActionBuilder
from environment.board import Board
from environment.economy import Economy
from environment.market import Market
from environment.state import GameState


class Planner:
    def __init__(
        self, state: GameState, config: AgentConfig | None = None
    ) -> None:
        self.state = state
        self.config = config or DEFAULT_CONFIG
        self.board = Board(state)
        self.eco = Economy(state)
        self.market = Market(state)
        self.scheduler = Scheduler(state)
        self.search = Search()

    def add(self, score: float, action: Action) -> None:
        self.search.add(score=score, action=action)

    def move_to(self, tile) -> Action:
        return move_to(self, tile)

    def choose(self) -> Action:
        return ActionBuilder.merge(
            *(n.action for n in self.search.topk(len(self.search.nodes)))
        )

    def play(self) -> Action:
        evaluate_market(self)
        evaluate_farming(self)
        evaluate_movement(self)
        evaluate_expansion(self)
        return self.choose()
