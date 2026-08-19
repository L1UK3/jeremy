from dataclasses import dataclass, field


@dataclass(slots=True)
class Action:
    score: float = 0.0

    farmer: list = field(default_factory=lambda: ["PASS"])
    hands: list = field(default_factory=list)
    market: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "farmer": self.farmer,
            "hands": self.hands,
            "market": self.market,
        }


class ActionBuilder:
    @staticmethod
    def pass_turn() -> Action:
        return Action()

    @staticmethod
    def move(direction: str, score: float = 0.0) -> Action:
        return Action(score=score, farmer=[direction])

    @staticmethod
    def harvest(score: float = 0.0) -> Action:
        return Action(score=score, farmer=["HARVEST"])

    @staticmethod
    def water(score: float = 0.0) -> Action:
        return Action(score=score, farmer=["WATER"])

    @staticmethod
    def plant(crop: str, score: float = 0.0) -> Action:
        return Action(score=score, farmer=["PLANT", crop])

    @staticmethod
    def dig(score: float = 0.0) -> Action:
        return Action(score=score, farmer=["DIG"])

    @staticmethod
    def fertilize(score: float = 0.0) -> Action:
        return Action(score=score, farmer=["FERTILIZE"])

    @staticmethod
    def pickup(item: str, amount: int = 1, score: float = 0.0) -> Action:
        return Action(score=score, farmer=["PICKUP", item, amount])

    @staticmethod
    def place(item: str, amount: int = 1, score: float = 0.0) -> Action:
        return Action(score=score, farmer=["PLACE", item, amount])

    @staticmethod
    def drop(score: float = 0.0) -> Action:
        return Action(score=score, farmer=["DROP"])

    @staticmethod
    def build_coop(score: float = 0.0) -> Action:
        return Action(score=score, farmer=["BUILD_COOP"])

    @staticmethod
    def build_pasture(score: float = 0.0) -> Action:
        return Action(score=score, farmer=["BUILD_PASTURE"])

    @staticmethod
    def feed(score: float = 0.0) -> Action:
        return Action(score=score, farmer=["FEED"])

    @staticmethod
    def care(score: float = 0.0) -> Action:
        return Action(score=score, farmer=["CARE"])

    @staticmethod
    def collect_fertilizer(score: float = 0.0) -> Action:
        return Action(score=score, farmer=["COLLECT_FERTILIZER"])

    @staticmethod
    def buy_seed(crop: str, amount: int = 1, score: float = 0.0) -> Action:
        a = Action(score=score)
        a.market.append(["BUY_SEED", crop, amount])
        return a

    @staticmethod
    def buy_product(item: str, amount: int = 1, score: float = 0.0) -> Action:
        a = Action(score=score)
        a.market.append(["BUY_PRODUCT", item, amount])
        return a

    @staticmethod
    def buy_animal(animal: str, amount: int = 1, score: float = 0.0) -> Action:
        a = Action(score=score)
        a.market.append(["BUY_ANIMAL", animal, amount])
        return a

    @staticmethod
    def sell(item: str, amount: int, score: float = 0.0) -> Action:
        a = Action(score=score)
        a.market.append(["SELL", item, amount])
        return a

    @staticmethod
    def buy_land(x: int, y: int, score: float = 0.0) -> Action:
        a = Action(score=score)
        a.market.append(["BUY_LAND", x, y])
        return a

    @staticmethod
    def hire_hand(score: float = 0.0) -> Action:
        a = Action(score=score)
        a.market.append(["HIRE"])
        return a

    @staticmethod
    def merge(*actions: Action) -> Action:
        result = Action()
        for a in actions:
            if a.score > result.score:
                result.score = a.score
            if a.farmer != ["PASS"] and result.farmer == ["PASS"]:
                result.farmer = a.farmer
            result.market.extend(a.market)
            result.hands.extend(a.hands)
        return result
