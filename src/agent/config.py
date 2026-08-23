"""
Configuration parameters for the rule-based heuristic agent.
Defines high-level strategy constants (e.g. target crop, sell threshold)
that can be overridden or controlled by higher-level models.
"""

from dataclasses import dataclass

from kaggle_environments.envs.kaggriculture.kaggriculture import CROPS


@dataclass(slots=True)
class AgentConfig:
    target_crop: str = "MELON"
    sell_threshold: int = 200
    seed_target: int = 1
    expand_land: bool = False
    max_hires_per_day: int = 0

    @property
    def seed_cost(self) -> int:
        return CROPS[self.target_crop]["seed"]

    @property
    def max_yield_day(self) -> int:
        return CROPS[self.target_crop]["max_yield_day"]


# Default global configuration instance
DEFAULT_CONFIG = AgentConfig()
