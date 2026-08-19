from agent.search import Search
from environment.actions import Action, ActionBuilder
from environment.board import Board
from environment.economy import Economy


class Planner:
    def __init__(self, state):
        self.state = state
        self.board = Board(state)
        self.eco = Economy(state)
        self.search = Search()

    # ----------------------------------------------------

    def add(self, score: float, action: Action) -> None:
        self.search.add(score=score, action=action)

    # ----------------------------------------------------

    def evaluate_market(self) -> None:
        crop = self.eco.best_crop()
        if crop is None:
            return

        if self.eco.should_sell(crop):
            self.add(50, ActionBuilder.sell(crop, self.eco.inventory(crop)))

        if self.eco.should_buy_seed(crop):
            self.add(40, ActionBuilder.buy_seed(crop, 1))

    # ----------------------------------------------------

    def evaluate_current_tile(self) -> None:
        tile = self.state.current_tile
        if not isinstance(tile, dict):
            return

        if tile.get("kind") != "PLANT":
            return

        if tile["yield_units"] > 0:
            value = tile["yield_units"] * self.eco.price(tile["crop"])
            self.add(100 + value, ActionBuilder.harvest())
            return

        if not tile["watered_today"]:
            self.add(80, ActionBuilder.water())

    # ----------------------------------------------------

    def evaluate_planting(self) -> None:
        if self.state.current_tile is not None:
            return

        crop = self.eco.best_crop()
        if crop is None:
            return

        if not self.state.has_seed(crop):
            return

        roi = self.eco.crop_roi(crop)
        self.add(60 + roi, ActionBuilder.plant(crop))

    # ----------------------------------------------------

    def evaluate_movement(self) -> None:
        target = self.board.nearest(self.board.harvestable())
        if target:
            self.add(40, self.move_to(target))
            return

        target = self.board.nearest(self.board.needs_water())
        if target:
            self.add(30, self.move_to(target))
            return

        target = self.board.nearest(self.board.empty_tiles())
        if target:
            self.add(20, self.move_to(target))

    # ----------------------------------------------------

    def evaluate_expansion(self) -> None:
        target = self.board.nearest(self.board.expandable())

        if self.eco.should_expand() and not target:
            self.add(10, self.move_to(target))
        else:
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
        self.search.dump()

        return self.choose()
