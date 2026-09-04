"""Kaggriculture agent entrypoint."""

from typing import Any

from policy import get_plan


def agent(obs: dict[str, Any]) -> dict[str, Any]:
    _plan: dict[str, Any] = get_plan(obs)

    # print(
    #     f"Day {obs['day']}: Crop={plan['crop']}, Crew={plan['crew']}, "
    #     f"Market={plan['market']}, Livestock={plan['livestock']}, "
    #     f"Predation={plan['predation']}"
    # )

    # Low-level turn actions (currently pass)
    return {"farmer": ["PASS"], "hands": [], "market": []}
