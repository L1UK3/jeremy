from planner import Planner
from state import GameState


def agent(obs):

    state = GameState.from_obs(obs)

    planner = Planner(state)

    return planner.play().to_dict()
