from dataclasses import dataclass, field


@dataclass(slots=True)
class Action:
    score: float = 0.0

    farmer: list = field(default_factory=lambda: ["PASS"])
    hands: list = field(default_factory=list)
    market: list = field(default_factory=list)

    def to_dict(self):
        return {
            "farmer": self.farmer,
            "hands": self.hands,
            "market": self.market,
        }


class ActionBuilder:

    @staticmethod
    def pass_turn():
        return Action()

    @staticmethod
    def move(direction, score=0):
        return Action(
            score=score,
            farmer=[direction],
        )

    @staticmethod
    def harvest(score=0):
        return Action(
            score=score,
            farmer=["HARVEST"],
        )

    @staticmethod
    def water(score=0):
        return Action(
            score=score,
            farmer=["WATER"],
        )

    @staticmethod
    def plant(crop, score=0):
        return Action(
            score=score,
            farmer=["PLANT", crop],
        )

    @staticmethod
    def dig(score=0):
        return Action(
            score=score,
            farmer=["DIG"],
        )

    @staticmethod
    def fertilize(score=0):
        return Action(
            score=score,
            farmer=["FERTILIZE"],
        )

    @staticmethod
    def buy_seed(crop, amount, score=0):
        a = Action(score=score)
        a.market.append(["BUY_SEED", crop, amount])
        return a

    @staticmethod
    def sell(item, amount, score=0):
        a = Action(score=score)
        a.market.append(["SELL", item, amount])
        return a

    @staticmethod
    def buy_quadrant(index, score=0):
        a = Action(score=score)
        a.market.append(["BUY_QUADRANT", index])
        return a

    @staticmethod
    def hire_hand(score=0):
        a = Action(score=score)
        a.market.append(["HIRE_FARMHAND"])
        return a

    @staticmethod
    def merge(*actions):
        result = Action()

        for a in actions:

            if a.score > result.score:
                result.score = a.score

            if a.farmer != ["PASS"]:
                result.farmer = a.farmer

            result.market.extend(a.market)
            result.hands.extend(a.hands)

        return result
