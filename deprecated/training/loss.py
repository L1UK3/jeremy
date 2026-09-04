"""Multi-task loss functions for Kaggriculture Behavioral Cloning."""

from __future__ import annotations

from typing import NamedTuple

import torch
import torch.nn as nn
import torch.nn.functional as F  # noqa: N812

__all__ = ["MacroLossBreakdown", "MacroMultiTaskLoss"]


class MacroLossBreakdown(NamedTuple):
    total_loss: torch.Tensor
    crop_loss: torch.Tensor
    crew_loss: torch.Tensor
    market_loss: torch.Tensor
    animal_loss: torch.Tensor
    predation_loss: torch.Tensor


class MacroMultiTaskLoss(nn.Module):
    def __init__(
        self,
        crop_weight: float = 1.0,
        crew_weight: float = 1.0,
        market_weight: float = 0.5,
        animal_weight: float = 0.8,
        predation_weight: float = 0.5,
    ) -> None:
        super().__init__()
        self.crop_weight = crop_weight
        self.crew_weight = crew_weight
        self.market_weight = market_weight
        self.animal_weight = animal_weight
        self.predation_weight = predation_weight

    def forward(
        self,
        logits: torch.Tensor,
        crop_targets: torch.Tensor,
        crew_targets: torch.Tensor,
        market_targets: torch.Tensor,
        animal_targets: torch.Tensor,
        predation_targets: torch.Tensor,
    ) -> MacroLossBreakdown:
        crop_logits = logits[:, 0:5]
        crew_logits = logits[:, 5:16]
        market_logits = logits[:, 16:20]
        animal_logits = logits[:, 20:24]
        predation_logits = logits[:, 24:27]

        crop_loss = F.cross_entropy(crop_logits, crop_targets)
        crew_loss = F.cross_entropy(crew_logits, crew_targets)
        market_loss = F.mse_loss(torch.sigmoid(market_logits), market_targets)
        animal_loss = F.cross_entropy(animal_logits, animal_targets)
        predation_loss = F.cross_entropy(predation_logits, predation_targets)

        total_loss = (
            self.crop_weight * crop_loss
            + self.crew_weight * crew_loss
            + self.market_weight * market_loss
            + self.animal_weight * animal_loss
            + self.predation_weight * predation_loss
        )

        return MacroLossBreakdown(
            total_loss=total_loss,
            crop_loss=crop_loss,
            crew_loss=crew_loss,
            market_loss=market_loss,
            animal_loss=animal_loss,
            predation_loss=predation_loss,
        )
