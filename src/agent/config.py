from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from environment.economy import Economy

__all__ = ["DEFAULT_CONFIG", "AgentConfig"]


@dataclass(slots=True)
class AgentConfig:
    target_crop: str = "MELON"
    seed_target: int = 4
    expand_land: bool = True
    max_hires_per_day: int = 8
    max_quadrants: int = 2

    def get_crop(self, eco: Economy) -> str | None:
        return eco.best_crop()


DEFAULT_CONFIG = AgentConfig()
