from agent.config import DEFAULT_CONFIG, AgentConfig
from agent.search import Search
from environment.actions import Action, ActionBuilder
from environment.board import Board
from environment.economy import Economy
from environment.state import GameState


class Planner:
    def __init__(
        self, state: GameState, config: AgentConfig | None = None
    ) -> None:
        self.state = state
        self.config = config or DEFAULT_CONFIG
        self.board = Board(state)
        self.eco = Economy(state)
        self.search = Search()

    # ----------------------------------------------------

    def add(self, score: float, action: Action) -> None:
        self.search.add(score=score, action=action)

    # ----------------------------------------------------

    def evaluate_market(self) -> None:
        crop = self.config.target_crop
        inventory = self.eco.inventory(crop)

        if inventory > 0 and self.eco.should_sell(
            crop, threshold=self.config.sell_threshold
        ):
            self.add(50, ActionBuilder.sell(crop, inventory))

        if self.eco.should_buy_seed(crop, target_count=self.config.seed_target):
            amount = self.config.seed_target - self.state.seed_count(crop)
            if amount > 0:
                self.add(40, ActionBuilder.buy_seed(crop, amount))

    # ----------------------------------------------------

    def evaluate_current_tile(self) -> None:
        tile = self.state.current_tile
        if not isinstance(tile, dict):
            return

        kind = tile.get("kind")

        if kind == "WEED":
            self.add(90, ActionBuilder.dig())
            return

        if kind != "PLANT":
            return

        crop = tile.get("crop")
        if crop == self.config.target_crop:
            planted_day = tile.get("planted_day")
            age = self.state.day - planted_day if planted_day is not None else 0
            yield_units = tile.get("yield_units", 0)

            # Harvest when crop reaches maximum yield day and has yield
            if age >= self.config.max_yield_day and yield_units > 0:
                value = yield_units * self.eco.price(self.config.target_crop)
                self.add(100 + value, ActionBuilder.harvest())
                return

            if not tile.get("watered_today", False):
                self.add(80, ActionBuilder.water())
                return

    # ----------------------------------------------------

    def evaluate_planting(self) -> None:
        if self.state.current_tile is not None:
            return

        crop = self.config.target_crop
        if not self.state.has_seed(crop):
            return

        roi = self.eco.crop_roi(crop)
        self.add(60 + roi, ActionBuilder.plant(crop))

    # ----------------------------------------------------

    def evaluate_movement(self) -> None:
        crop = self.config.target_crop

        # Move to harvestable crop
        target = self.board.nearest(self.board.harvestable(crop))
        if target:
            self.add(40, self.move_to(target))
            return

        # Move to thirsty crop
        target = self.board.nearest(self.board.needs_water(crop))
        if target:
            self.add(30, self.move_to(target))
            return

        # Move to empty tile if seeds are available
        if self.state.has_seed(crop):
            target = self.board.nearest(self.board.empty_tiles())
            if target:
                self.add(20, self.move_to(target))

    # ----------------------------------------------------

    def evaluate_expansion(self) -> None:
        if not self.config.expand_land:
            return

        target = self.board.nearest(self.board.empty_tiles())
        if not self.eco.should_expand() or target is None:
            return

        self.add(100, ActionBuilder.buy_land(target.x, target.y))

    # ----------------------------------------------------

    def move_to(self, tile) -> Action:
        fx, fy = self.state.farmer
        if fx > tile.x:
            return ActionBuilder.move("WEST")
        if fx < tile.x:
            return ActionBuilder.move("EAST")
        if fy > tile.y:
            return ActionBuilder.move("NORTH")
        if fy < tile.y:
            return ActionBuilder.move("SOUTH")
        return ActionBuilder.pass_turn()

    # ----------------------------------------------------

    def choose(self) -> Action:
        return ActionBuilder.merge(
            *(n.action for n in self.search.topk(len(self.search.nodes)))
        )

    # ----------------------------------------------------

    def play(self) -> Action:
        self.evaluate_market()
        self.evaluate_current_tile()
        self.evaluate_planting()
        self.evaluate_movement()
        self.evaluate_expansion()

        return self.choose()
