from typing import Any

from v2.main import agent


def kaggle_submission_agent(obs: dict[str, Any]) -> dict[str, Any]:
    """Kaggle submission agent entrypoint."""
    return agent(obs)
