from src.sample.buddy.planner import Planner
from src.sample.buddy.state import GameState


def agent(obs):

    state = GameState.from_obs(obs)

    planner = Planner(state)

    return planner.play().to_dict()
