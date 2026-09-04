"""PyTorch Macro Policy Network for Kaggriculture Behavioral Cloning."""

from __future__ import annotations

from typing import NamedTuple

import torch
import torch.nn as nn
import torch.nn.functional as F  # noqa: N812

__all__ = ["MacroOutput", "MacroPolicyMLP"]


class MacroOutput(NamedTuple):
    crop_logits: torch.Tensor
    crew_logits: torch.Tensor
    market_logits: torch.Tensor
    animal_logits: torch.Tensor
    predation_logits: torch.Tensor
    full_logits: torch.Tensor


class MacroPolicyMLP(nn.Module):
    def __init__(
        self,
        in_features: int = 1706,
        hidden_1: int = 256,
        hidden_2: int = 128,
        out_features: int = 35,
    ) -> None:
        super().__init__()
        self.in_features = in_features
        self.hidden_1 = hidden_1
        self.hidden_2 = hidden_2
        self.out_features = out_features

        self.fc1 = nn.Linear(in_features, hidden_1)
        self.fc2 = nn.Linear(hidden_1, hidden_2)
        self.fc_out = nn.Linear(hidden_2, out_features)

        self.apply(self._init_weights)

    @staticmethod
    def _init_weights(module: nn.Module) -> None:
        if isinstance(module, nn.Linear):
            nn.init.kaiming_normal_(
                module.weight, mode="fan_in", nonlinearity="relu"
            )
            if module.bias is not None:
                nn.init.zeros_(module.bias)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.fc_out(F.relu(self.fc2(F.relu(self.fc1(x)))))

    def decode_heads(self, logits: torch.Tensor) -> MacroOutput:
        crop_logits = logits[:, 0:5]
        crew_logits = logits[:, 5:16]
        market_logits = logits[:, 16:20]
        animal_logits = logits[:, 20:24]
        predation_logits = logits[:, 24:27]
        return MacroOutput(
            crop_logits=crop_logits,
            crew_logits=crew_logits,
            market_logits=market_logits,
            animal_logits=animal_logits,
            predation_logits=predation_logits,
            full_logits=logits,
        )
