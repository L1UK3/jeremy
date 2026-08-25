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
    sell_threshold: int = 180
    seed_target: int = 12
    expand_land: bool = True
    max_hires_per_day: int = 3
    dynamic_crops: bool = True
    max_hires_per_day: int = 6
    max_quadrants: int = 2

    @property
    def seed_cost(self) -> int:
        return CROPS[self.target_crop]["seed"]

    @property
    def max_yield_day(self) -> int:
        return CROPS[self.target_crop]["max_yield_day"]


# Default global configuration instance
DEFAULT_CONFIG = AgentConfig()
