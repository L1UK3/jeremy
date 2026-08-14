from dataclasses import dataclass

from board import Board
from economy import Economy
from actions import ActionBuilder


@dataclass(slots=True)
class Candidate:
    score: float
    action: object


class Planner:

    def __init__(self, state):

        self.state = state
        self.board = Board(state)
        self.eco = Economy(state)

        self.candidates = []

    # ----------------------------------------------------

    def add(self, score, action):

        self.candidates.append(
            Candidate(score, action)
        )

    # ----------------------------------------------------

    def evaluate_market(self):

        crop = self.eco.best_crop()

        if self.eco.should_sell(crop):

            self.add(
                50,
                ActionBuilder.sell(
                    crop,
                    self.eco.inventory(crop)
                )
            )

        if self.eco.should_buy_seed(crop):

            self.add(
                40,
                ActionBuilder.buy_seed(
                    crop,
                    1
                )
            )

    # ----------------------------------------------------

    def evaluate_current_tile(self):

        tile = self.state.current_tile

        if not isinstance(tile, dict):
            return

        if tile.get("kind") != "PLANT":
            return

        if tile["yield_units"] > 0:

            value = (
                tile["yield_units"]
                * self.eco.price(tile["crop"])
            )

            self.add(
                100 + value,
                ActionBuilder.harvest()
            )

            return

        if not tile["watered_today"]:

            self.add(
                80,
                ActionBuilder.water()
            )

    # ----------------------------------------------------

    def evaluate_planting(self):

        if self.state.current_tile is not None:
            return

        crop = self.eco.best_crop()

        if not self.state.has_seed(crop):
            return

        roi = self.eco.crop_roi(crop)

        self.add(
            60 + roi,
            ActionBuilder.plant(crop)
        )

    # ----------------------------------------------------

    def evaluate_movement(self):

        target = self.board.nearest(
            self.board.harvestable()
        )

        if target:

            self.add(
                40,
                self.move_to(target)
            )

            return

        target = self.board.nearest(
            self.board.needs_water()
        )

        if target:

            self.add(
                30,
                self.move_to(target)
            )

            return

        target = self.board.nearest(
            self.board.empty_tiles()
        )

        if target:

            self.add(
                20,
                self.move_to(target)
            )

    # ----------------------------------------------------

    def move_to(self, tile):

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

    def choose(self):

        if not self.candidates:
            return ActionBuilder.pass_turn()

        self.candidates.sort(
            key=lambda c: c.score,
            reverse=True,
        )

        farmer = None
        market = []

        for candidate in self.candidates:

            action = candidate.action

            if farmer is None and action.farmer != ["PASS"]:
                farmer = action

            market.extend(action.market)

        if farmer is None:
            farmer = ActionBuilder.pass_turn()

        farmer.market = market

        return farmer

    # ----------------------------------------------------

    def play(self):

        self.evaluate_market()

        self.evaluate_current_tile()

        self.evaluate_planting()

        self.evaluate_movement()

        return self.choose()
