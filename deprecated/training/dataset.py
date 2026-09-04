"""Dataset loaders and preprocessing for Kaggriculture Behavioral Cloning."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import Dataset

__all__ = ["KaggricultureReplayDataset", "ReplayBatch"]


@dataclass(frozen=True, slots=True)
class ReplayBatch:
    features: torch.Tensor
    crop_targets: torch.Tensor
    crew_targets: torch.Tensor
    market_targets: torch.Tensor
    target_animals: torch.Tensor
    crop_weights: torch.Tensor
    predation_mode: torch.Tensor


class KaggricultureReplayDataset(Dataset):
    def __init__(
        self,
        features: np.ndarray,
        crop_targets: np.ndarray,
        crew_targets: np.ndarray,
        market_targets: np.ndarray,
        target_animals: np.ndarray | None = None,
        crop_weights: np.ndarray | None = None,
        predation_mode: np.ndarray | None = None,
    ) -> None:
        self.features = torch.as_tensor(features, dtype=torch.float32)
        self.crop_targets = torch.as_tensor(crop_targets, dtype=torch.int64)
        self.crew_targets = torch.as_tensor(crew_targets, dtype=torch.int64)
        self.market_targets = torch.as_tensor(
            market_targets, dtype=torch.float32
        )
        n = len(self.features)
        self.target_animals = torch.as_tensor(
            target_animals if target_animals is not None else np.zeros(n, dtype=np.int64),
            dtype=torch.int64,
        )
        self.crop_weights = torch.as_tensor(
            crop_weights if crop_weights is not None else np.ones((n, 5), dtype=np.float32),
            dtype=torch.float32,
        )
        self.predation_mode = torch.as_tensor(
            predation_mode if predation_mode is not None else np.zeros(n, dtype=np.int64),
            dtype=torch.int64,
        )

    def __len__(self) -> int:
        return len(self.features)

    def __getitem__(
        self, idx: int
    ) -> tuple[
        torch.Tensor,
        torch.Tensor,
        torch.Tensor,
        torch.Tensor,
        torch.Tensor,
        torch.Tensor,
    ]:
        return (
            self.features[idx],
            self.crop_targets[idx],
            self.crew_targets[idx],
            self.market_targets[idx],
            self.target_animals[idx],
            self.predation_mode[idx],
        )

    @classmethod
    def from_npz(cls, npz_path: Path | str) -> KaggricultureReplayDataset:
        data = np.load(str(npz_path))
        return cls(
            features=data["features"],
            crop_targets=data["crop_targets"],
            crew_targets=data["crew_targets"],
            market_targets=data["market_targets"],
            target_animals=data.get("target_animals"),
            crop_weights=data.get("crop_weights"),
            predation_mode=data.get("predation_mode"),
        )

