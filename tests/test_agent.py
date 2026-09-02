from main import agent, kaggle_submission_entrypoint
from trajectories.trace import FLAT_TRACE


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


def test_trace_loaded_properly():
    assert len(FLAT_TRACE) == 720
    assert "farmer" in FLAT_TRACE[0]
    assert "hands" in FLAT_TRACE[0]
    assert "market" in FLAT_TRACE[0]


def test_agent_phases_and_kaggle_entrypoint():
    # 1. Opening step (step 0)
    obs_open = _sample_obs(step=0)
    act_open = agent(obs_open)
    act_kaggle = kaggle_submission_entrypoint(obs_open)
    assert act_open == act_kaggle
    assert "farmer" in act_open and "market" in act_open

    # 2. Mid game step (step 50)
    obs_mid = _sample_obs(step=50)
    act_mid = agent(obs_mid)
    assert isinstance(act_mid, dict)
    assert "farmer" in act_mid

    # 3. Penultimate day step (step 680)
    obs_penult = _sample_obs(step=680)
    act_penult = agent(obs_penult)
    assert isinstance(act_penult, dict)
    assert "farmer" in act_penult

    # 4. Explosion endgame step (step 715)
    obs_end = _sample_obs(step=715)
    act_explosion = agent(obs_end)
    assert isinstance(act_explosion, dict)
    assert "farmer" in act_explosion

