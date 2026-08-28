from __future__ import annotations

from src.v0.agent.config import DEFAULT_CONFIG, AgentConfig
from src.v0.agent.evaluators import evaluate_expansion, evaluate_market
from src.v0.agent.expansion import EXPANSION_TRACE
from src.v0.agent.explosion import explosion
from src.v0.agent.jobs import schedule_jobs
from src.v0.agent.manage_livestock import manage_livestock
from src.v0.agent.opening import OPENING_TRACE
from src.v0.agent.scheduler import Scheduler
from src.v0.agent.search import Search
from src.v0.environment.actions import Action, ActionBuilder
from src.v0.environment.board import Board
from src.v0.environment.economy import Economy
from src.v0.environment.market import Market
from src.v0.environment.state import GameState

__all__ = ["Planner"]


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

    def choose(self) -> Action:
        return ActionBuilder.merge(
            *(n.action for n in self.search.topk(len(self.search.nodes)))
        )

    def play(self) -> Action:
        step = self.state.step
        if step in OPENING_TRACE:
            act = OPENING_TRACE[step]
            return Action(
                farmer=act.get("farmer", ["PASS"]),
                hands=act.get("hands", []),
                market=act.get("market", []),
            )

        if step in EXPANSION_TRACE:
            act = EXPANSION_TRACE[step]
            return Action(
                farmer=act.get("farmer", ["PASS"]),
                hands=act.get("hands", []),
                market=act.get("market", []),
            )

        if step >= (720 - 8):
            return explosion(self)

        evaluate_market(self)
        evaluate_expansion(self)
        market_action = self.choose()

        livestock_act = manage_livestock(
            self, worker_idx=0, worker_pos=self.state.farmer
        )

        schedule_jobs(self)
        default_farmer_act, hands_acts = self.scheduler.assign()

        farmer_act = (
            livestock_act if livestock_act is not None else default_farmer_act
        )

        return Action(
            farmer=farmer_act,
            hands=hands_acts,
            market=market_action.market,
        )
