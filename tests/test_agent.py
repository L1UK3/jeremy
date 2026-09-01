from src.main import (
    agent,
    expansion_agent,
    explosion_agent,
    main_agent,
    opening_agent,
)
from src.main import agent, kaggle_submission_entrypoint
from src.trace import FLAT_TRACE


def _sample_obs(step: int = 0) -> dict:
    return {
        "player": 0,
        "step": step,
        "day": step // 24,
        "hour": step % 24,
        "market": {"prices": {"WHEAT": 25, "CARROT": 35, "MELON": 250}},
        "farms": [
            {
                "money": 3000,
                "farmer": [4, 4],
                "hands": [],
                "unlocked_quadrants": ["NW"],
                "tiles": [[None for _ in range(10)] for _ in range(10)],
            }
        ],
        "private": {"shed": {}, "seeds": {}},
    }


def test_agent_first_step():
    obs = _sample_obs(step=0)
    action = agent(obs)
    assert isinstance(action, dict)
    assert "farmer" in action
    assert "hands" in action
    assert "market" in action
    assert len(action["market"]) <= 10


def test_routes_loaded_from_json():
    from src.main import ROUTES
def test_trace_loaded_properly():
    assert len(FLAT_TRACE) == 720
    assert "farmer" in FLAT_TRACE[0]
    assert "hands" in FLAT_TRACE[0]
    assert "market" in FLAT_TRACE[0]

    assert isinstance(ROUTES, dict)
    assert len(ROUTES) == 48
    assert 0 in ROUTES
    assert 169 in ROUTES
    assert "farmer" in ROUTES[0]
    assert "hands" in ROUTES[0]
    assert "market" in ROUTES[0]


def test_sub_agents_and_wrapper_routing():
    # 1. Opening agent (step 0)
def test_agent_phases_and_kaggle_entrypoint():
    # 1. Opening step (step 0)
    obs_open = _sample_obs(step=0)
    act_open = opening_agent(obs_open)
    act_wrapper_open = agent(obs_open)
    assert act_open == act_wrapper_open
    act_open = agent(obs_open)
    act_kaggle = kaggle_submission_entrypoint(obs_open)
    assert act_open == act_kaggle
    assert "farmer" in act_open and "market" in act_open

    # 2. Main agent (step 50 - mid game)
    # 2. Mid game step (step 50)
    obs_mid = _sample_obs(step=50)
    act_main = main_agent(obs_mid)
    act_wrapper_mid = agent(obs_mid)
    assert act_main == act_wrapper_mid
    assert "farmer" in act_main
    act_mid = agent(obs_mid)
    assert isinstance(act_mid, dict)
    assert "farmer" in act_mid

    # 3. Expansion agent (step 169 - NE expansion scripted turn)
    obs_exp = _sample_obs(step=169)
    act_exp = expansion_agent(obs_exp)
    act_wrapper_exp = agent(obs_exp)
    assert act_exp == act_wrapper_exp
    assert any(order[0] == "BUY_LAND" for order in act_exp["market"])
    # 3. Penultimate day step (step 680)
    obs_penult = _sample_obs(step=680)
    act_penult = agent(obs_penult)
    assert isinstance(act_penult, dict)
    assert "farmer" in act_penult

    # 4. Explosion agent (step 715 - endgame liquidation)
    # 4. Explosion endgame step (step 715)
    obs_end = _sample_obs(step=715)
    act_explosion = explosion_agent(obs_end)
    act_wrapper_end = agent(obs_end)
    assert act_explosion == act_wrapper_end
    act_explosion = agent(obs_end)
    assert isinstance(act_explosion, dict)
    assert "farmer" in act_explosion
