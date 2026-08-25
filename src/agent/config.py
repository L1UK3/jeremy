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
    seed_target: int = 12
    expand_land: bool = True
    max_hires_per_day: int = 3
    dynamic_crops: bool = True
    max_quadrants: int = 2

    def get_crop(self, eco) -> str:
        """Resolve the target crop dynamically using live ROI if enabled."""
        if self.dynamic_crops:
            return eco.best_crop() or self.target_crop
        return self.target_crop


# Default global configuration instance
DEFAULT_CONFIG = AgentConfig()

