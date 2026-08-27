"""
Configuration parameters for the rule-based heuristic agent.
Defines high-level strategy constants (e.g. target crop, sell threshold)
that can be overridden or controlled by higher-level models.
"""

from dataclasses import dataclass


@dataclass(slots=True)
class AgentConfig:
    target_crop: str = "MELON"
    seed_target: int = 4
    expand_land: bool = True
    max_hires_per_day: int = 8
    max_quadrants: int = 2

    def get_crop(self, eco) -> str | None:
        return eco.best_crop()


DEFAULT_CONFIG = AgentConfig()
