"""Train neural Macro Policy via supervised imitation and export deployable weights.

Trains a 2-layer MLP on extracted replay observations and exports weights matching
the runtime shape requirements of src/model/policy.py.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from torch.nn.functional import cross_entropy, relu, smooth_l1_loss
from torch.utils.data import DataLoader, Dataset

# Ensure project root is on sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from data.imitation import load_imitation_dataset, save_imitation_dataset

DEFAULT_DATA_PATH = ROOT / ".out" / "imitation_dataset.npz"
DEFAULT_CHECKPOINT_DIR = ROOT / ".out" / "checkpoints"
DEFAULT_PRODUCTION_WEIGHTS = ROOT / "src" / "model" / "model_weights.npz"


class MacroPolicyNet(nn.Module):
    """2-layer multi-task MLP policy predicting economic intent from farm state."""

    def __init__(
        self,
        input_dim: int = 1706,
        hidden_1: int = 256,
        hidden_2: int = 128,
        output_dim: int = 35,
    ) -> None:
        super().__init__()
        self.fc1 = nn.Linear(input_dim, hidden_1)
        self.fc2 = nn.Linear(hidden_1, hidden_2)
        self.fc_out = nn.Linear(hidden_2, output_dim)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        h1 = relu(self.fc1(x))
        h2 = relu(self.fc2(h1))
        return self.fc_out(h2)


class ImitationDataset(Dataset):
    """PyTorch dataset wrapping imitation observation features and multi-head targets."""

    def __init__(
        self, features: np.ndarray, targets: dict[str, np.ndarray]
    ) -> None:
        self.features = torch.from_numpy(features).float()
        self.crop = torch.from_numpy(targets["crop"]).long()
        self.crew = torch.from_numpy(targets["crew"]).long()
        self.livestock = torch.from_numpy(targets["livestock"]).long()
        self.predation = torch.from_numpy(targets["predation"]).long()
        self.market = torch.from_numpy(targets["market"]).float()

    def __len__(self) -> int:
        return self.features.size(0)

    def __getitem__(
        self, idx: int
    ) -> tuple[torch.Tensor, dict[str, torch.Tensor]]:
        target = {
            "crop": self.crop[idx],
            "crew": self.crew[idx],
            "livestock": self.livestock[idx],
            "predation": self.predation[idx],
            "market": self.market[idx],
        }
        return self.features[idx], target


def compute_loss(
    logits: torch.Tensor,
    targets: dict[str, torch.Tensor],
    class_weights_crop: torch.Tensor | None = None,
) -> tuple[torch.Tensor, dict[str, float]]:
    """Compute balanced compound loss across all 5 macro intent heads."""
    loss_crop = cross_entropy(
        logits[:, 0:5], targets["crop"], weight=class_weights_crop
    )
    loss_crew = cross_entropy(logits[:, 5:16], targets["crew"])
    loss_market = smooth_l1_loss(logits[:, 16:20], targets["market"])
    loss_livestock = cross_entropy(logits[:, 20:24], targets["livestock"])
    loss_predation = cross_entropy(logits[:, 24:27], targets["predation"])


    total_loss = (
        1.0 * loss_crop
        + 0.8 * loss_crew
        + 0.5 * loss_market
        + 0.5 * loss_livestock
        + 0.5 * loss_predation
    )

    loss_dict = {
        "crop": float(loss_crop.item()),
        "crew": float(loss_crew.item()),
        "market": float(loss_market.item()),
        "livestock": float(loss_livestock.item()),
        "predation": float(loss_predation.item()),
        "total": float(total_loss.item()),
    }
    return total_loss, loss_dict


def export_to_npz(model: MacroPolicyNet, out_path: Path | str) -> None:
    """Export model weights to .npz matching runtime numpy forward pass expectations."""
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)

    w1 = model.fc1.weight.t().detach().cpu().numpy().astype(np.float64)
    b1 = model.fc1.bias.detach().cpu().numpy().astype(np.float32)

    w2 = model.fc2.weight.t().detach().cpu().numpy().astype(np.float64)
    b2 = model.fc2.bias.detach().cpu().numpy().astype(np.float32)

    w_out = model.fc_out.weight.t().detach().cpu().numpy().astype(np.float64)
    b_out = model.fc_out.bias.detach().cpu().numpy().astype(np.float32)

    np.savez_compressed(
        p,
        w1=w1,
        b1=b1,
        w2=w2,
        b2=b2,
        w_out=w_out,
        b_out=b_out,
    )


def load_or_create_dataset(
    data_path: Path | str, fallback_samples: int = 240
) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    """Load pre-extracted imitation dataset or synthesize a structured baseline dataset."""
    p = Path(data_path)
    if p.is_file():
        return load_imitation_dataset(p)

    print(
        f"Dataset not found at {p}. Generating synthetic baseline dataset ({fallback_samples} samples)..."
    )
    rng = np.random.default_rng(42)
    features = rng.standard_normal((fallback_samples, 1706)).astype(np.float32)
    targets = {
        "crop": rng.choice(5, size=(fallback_samples,)),
        "crew": rng.choice(11, size=(fallback_samples,)),
        "livestock": rng.choice(4, size=(fallback_samples,)),
        "predation": rng.choice(3, size=(fallback_samples,)),
        "market": rng.uniform(0.5, 1.5, size=(fallback_samples, 4)).astype(
            np.float32
        ),
    }
    save_imitation_dataset(features, targets, p)
    return features, targets


def train_policy(
    data_path: Path | str = DEFAULT_DATA_PATH,
    checkpoint_dir: Path | str = DEFAULT_CHECKPOINT_DIR,
    update_main: bool = True,
    epochs: int = 15,
    batch_size: int = 64,
    lr: float = 1e-3,
    seed: int = 42,
) -> Path:
    """Execute complete training cycle and export validated checkpoints."""
    torch.manual_seed(seed)
    np.random.seed(seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Training Macro Policy on {device}...")

    features, targets = load_or_create_dataset(data_path)
    n_samples = features.shape[0]

    # Compute inverse class weights for crop
    counts = Counter(targets["crop"])
    weights = np.array(
        [1.0 / max(1, counts.get(c, 1)) for c in range(5)], dtype=np.float32
    )
    weights = weights / weights.sum() * 5.0
    class_weights_crop = torch.from_numpy(weights).to(device)

    # 80/20 train/val split
    indices = np.arange(n_samples)
    np.random.shuffle(indices)
    split = int(0.8 * n_samples)
    train_idx, val_idx = indices[:split], indices[split:]

    train_ds = ImitationDataset(
        features[train_idx], {k: v[train_idx] for k, v in targets.items()}
    )
    val_ds = ImitationDataset(
        features[val_idx], {k: v[val_idx] for k, v in targets.items()}
    )

    train_loader = DataLoader(
        train_ds, batch_size=min(batch_size, len(train_ds)), shuffle=True
    )
    val_loader = DataLoader(
        val_ds, batch_size=min(batch_size, len(val_ds)), shuffle=False
    )

    model = MacroPolicyNet().to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer, T_max=epochs
    )

    ckpt_dir = Path(checkpoint_dir)
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    best_val_loss = float("inf")
    best_weights_path = ckpt_dir / "best_model_weights.npz"

    for epoch in range(1, epochs + 1):
        model.train()
        train_loss = 0.0

        for x_batch, y_batch in train_loader:
            x_batch = x_batch.to(device)
            y_batch = {k: v.to(device) for k, v in y_batch.items()}

            optimizer.zero_grad(set_to_none=True)
            logits = model(x_batch)
            loss, _ = compute_loss(logits, y_batch, class_weights_crop)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
            train_loss += loss.item() * x_batch.size(0)

        scheduler.step()
        train_loss /= max(1, len(train_ds))

        model.eval()
        val_loss = 0.0
        val_details: dict[str, float] = {}
        with torch.no_grad():
            for x_val, y_val in val_loader:
                x_val = x_val.to(device)
                y_val = {k: v.to(device) for k, v in y_val.items()}
                logits = model(x_val)
                v_loss, d_dict = compute_loss(logits, y_val, class_weights_crop)
                val_loss += v_loss.item() * x_val.size(0)
                for k, v in d_dict.items():
                    val_details[k] = val_details.get(k, 0.0) + v

        val_loss /= max(1, len(val_ds))
        print(
            f"Epoch {epoch:02d}/{epochs} | Train Loss: {train_loss:.4f} | Val Loss: {val_loss:.4f}"
        )

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            export_to_npz(model, best_weights_path)
            print(f"  &rarr; Saved best checkpoint to {best_weights_path}")

    if update_main and best_weights_path.is_file():
        shutil.copyfile(best_weights_path, DEFAULT_PRODUCTION_WEIGHTS)
        print(
            f"Updated production model weights at {DEFAULT_PRODUCTION_WEIGHTS}"
        )

    return best_weights_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Train Kaggriculture Macro Policy neural network."
    )
    parser.add_argument(
        "--data-path",
        type=str,
        default=str(DEFAULT_DATA_PATH),
        help="Path to imitation dataset .npz",
    )
    parser.add_argument(
        "--checkpoint-dir",
        type=str,
        default=str(DEFAULT_CHECKPOINT_DIR),
        help="Directory to store checkpoints",
    )
    parser.add_argument(
        "--epochs", type=int, default=15, help="Number of training epochs"
    )
    parser.add_argument("--batch-size", type=int, default=64, help="Batch size")
    parser.add_argument("--lr", type=float, default=1e-3, help="Learning rate")
    parser.add_argument(
        "--no-update-main",
        action="store_true",
        help="Do not overwrite src/model/model_weights.npz",
    )

    args = parser.parse_args()
    train_policy(
        data_path=Path(args.data_path),
        checkpoint_dir=Path(args.checkpoint_dir),
        update_main=not args.no_update_main,
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr,
    )


if __name__ == "__main__":
    main()
