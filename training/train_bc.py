"""Behavioral Cloning training loop with best practices (AMP, Cosine Annealing, Checkpointing)."""

from __future__ import annotations

import argparse
import random
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, random_split

from training.dataset import KaggricultureReplayDataset
from training.export import export_torch_to_npz, verify_parity
from training.loss import MacroMultiTaskLoss
from training.model import MacroPolicyMLP

__all__ = ["TrainingConfig", "train_bc"]


@dataclass
class TrainingConfig:
    dataset_path: str = "data/demos/bc_train_dataset.npz"
    output_npz_path: str = "src/models/model_weights.npz"
    checkpoint_dir: str = "checkpoints"
    batch_size: int = 64
    epochs: int = 50
    learning_rate: float = 1e-3
    weight_decay: float = 1e-4
    val_split: float = 0.2
    seed: int = 42
    device: str = "cuda" if torch.cuda.is_available() else "cpu"


def set_seed(seed: int = 42) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False


def train_one_epoch(
    model: nn.Module,
    dataloader: DataLoader,
    optimizer: torch.optim.Optimizer,
    criterion: MacroMultiTaskLoss,
    device: torch.device,
    scaler: torch.amp.GradScaler | None = None,
) -> float:
    model.train()
    total_loss = 0.0

    for features, crop_t, crew_t, market_t, animal_t, pred_t in dataloader:
        features = features.to(device, non_blocking=True)
        crop_t = crop_t.to(device, non_blocking=True)
        crew_t = crew_t.to(device, non_blocking=True)
        market_t = market_t.to(device, non_blocking=True)
        animal_t = animal_t.to(device, non_blocking=True)
        pred_t = pred_t.to(device, non_blocking=True)

        optimizer.zero_grad(set_to_none=True)

        with torch.amp.autocast(
            device_type=device.type, enabled=scaler is not None
        ):
            logits = model(features)
            breakdown = criterion(
                logits, crop_t, crew_t, market_t, animal_t, pred_t
            )
            loss = breakdown.total_loss

        if scaler is not None:
            scaler.scale(loss).backward()
            scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            scaler.step(optimizer)
            scaler.update()
        else:
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()

        total_loss += loss.item()

    return total_loss / len(dataloader)


@torch.no_grad()
def evaluate(
    model: nn.Module,
    dataloader: DataLoader,
    criterion: MacroMultiTaskLoss,
    device: torch.device,
) -> tuple[float, float, float, float, float]:
    model.eval()
    total_loss = 0.0
    crop_correct = 0
    crew_correct = 0
    animal_correct = 0
    pred_correct = 0
    total_samples = 0

    for features, crop_t, crew_t, market_t, animal_t, pred_t in dataloader:
        features = features.to(device, non_blocking=True)
        crop_t = crop_t.to(device, non_blocking=True)
        crew_t = crew_t.to(device, non_blocking=True)
        market_t = market_t.to(device, non_blocking=True)
        animal_t = animal_t.to(device, non_blocking=True)
        pred_t = pred_t.to(device, non_blocking=True)

        logits = model(features)
        breakdown = criterion(
            logits, crop_t, crew_t, market_t, animal_t, pred_t
        )
        total_loss += breakdown.total_loss.item()

        heads = model.decode_heads(logits)
        crop_preds = heads.crop_logits.argmax(dim=-1)
        crew_preds = heads.crew_logits.argmax(dim=-1)
        animal_preds = heads.animal_logits.argmax(dim=-1)
        pred_preds = heads.predation_logits.argmax(dim=-1)

        crop_correct += (crop_preds == crop_t).sum().item()
        crew_correct += (crew_preds == crew_t).sum().item()
        animal_correct += (animal_preds == animal_t).sum().item()
        pred_correct += (pred_preds == pred_t).sum().item()
        total_samples += features.size(0)

    avg_loss = total_loss / len(dataloader)
    n = max(1, total_samples)
    return (
        avg_loss,
        crop_correct / n,
        crew_correct / n,
        animal_correct / n,
        pred_correct / n,
    )


def train_bc(config: TrainingConfig | None = None) -> float:
    if config is None:
        config = TrainingConfig()

    set_seed(config.seed)
    device = torch.device(config.device)
    if device.type == "cuda" and torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        print(f"Using device: {device} ({gpu_name})")
    else:
        print(f"Using device: {device}")


    dataset = KaggricultureReplayDataset.from_npz(config.dataset_path)
    val_size = max(1, int(len(dataset) * config.val_split))
    train_size = len(dataset) - val_size
    train_ds, val_ds = random_split(dataset, [train_size, val_size])

    train_loader = DataLoader(
        train_ds,
        batch_size=config.batch_size,
        shuffle=True,
        pin_memory=(device.type == "cuda"),
    )
    val_loader = DataLoader(
        val_ds,
        batch_size=config.batch_size,
        shuffle=False,
        pin_memory=(device.type == "cuda"),
    )

    model = MacroPolicyMLP().to(device)
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=config.learning_rate,
        weight_decay=config.weight_decay,
    )
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer, T_max=config.epochs, eta_min=1e-5
    )
    criterion = MacroMultiTaskLoss()
    scaler = (
        torch.amp.GradScaler(device.type) if device.type == "cuda" else None
    )

    best_val_loss = float("inf")
    best_checkpoint_path = Path(config.checkpoint_dir) / "best_model.pt"
    best_checkpoint_path.parent.mkdir(parents=True, exist_ok=True)

    print(
        f"Training on {train_size} samples, validating on {val_size} samples for {config.epochs} epochs..."
    )

    for epoch in range(1, config.epochs + 1):
        train_loss = train_one_epoch(
            model, train_loader, optimizer, criterion, device, scaler
        )
        val_loss, crop_acc, crew_acc, anim_acc, pred_acc = evaluate(
            model, val_loader, criterion, device
        )
        scheduler.step()

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            torch.save(
                {
                    "epoch": epoch,
                    "model_state_dict": model.state_dict(),
                    "optimizer_state_dict": optimizer.state_dict(),
                    "val_loss": val_loss,
                    "crop_acc": crop_acc,
                    "crew_acc": crew_acc,
                    "anim_acc": anim_acc,
                    "pred_acc": pred_acc,
                },
                str(best_checkpoint_path),
            )

        if epoch % 5 == 0 or epoch == config.epochs:
            print(
                f"Epoch {epoch:03d}/{config.epochs} | "
                f"Train Loss: {train_loss:.4f} | "
                f"Val Loss: {val_loss:.4f} (Best: {best_val_loss:.4f}) | "
                f"Crop: {crop_acc * 100:.1f}% | Crew: {crew_acc * 100:.1f}% | "
                f"Anim: {anim_acc * 100:.1f}% | Pred: {pred_acc * 100:.1f}%"
            )

    checkpoint = torch.load(
        str(best_checkpoint_path), map_location="cpu", weights_only=True
    )
    model.load_state_dict(checkpoint["model_state_dict"])
    model.cpu()

    export_torch_to_npz(model, config.output_npz_path)
    parity_diff = verify_parity(model, config.output_npz_path)
    print(f"\nExported weights to {config.output_npz_path}")
    print(f"PyTorch <-> NumPy Parity Max Diff: {parity_diff:.8f}")
    assert parity_diff < 1e-5, f"Parity diff too large: {parity_diff}"

    return best_val_loss


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Train Behavioral Cloning Macro Policy"
    )
    parser.add_argument(
        "--dataset", type=str, default="data/demos/bc_train_dataset.npz"
    )
    parser.add_argument(
        "--output", type=str, default="src/models/model_weights.npz"
    )
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--device",
        type=str,
        default=None,
        help="Device to train on (cuda or cpu; defaults to auto-detect)",
    )
    args = parser.parse_args()

    kwargs: dict[str, Any] = {
        "dataset_path": args.dataset,
        "output_npz_path": args.output,
        "epochs": args.epochs,
        "batch_size": args.batch_size,
        "learning_rate": args.lr,
        "seed": args.seed,
    }
    if args.device is not None:
        kwargs["device"] = args.device

    cfg = TrainingConfig(**kwargs)
    train_bc(cfg)

