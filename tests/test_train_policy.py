"""Unit tests for Macro Policy neural training, loss balancing, and weight export."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import torch

from scripts.train_policy import (
    MacroPolicyNet,
    compute_loss,
    export_to_npz,
    load_or_create_dataset,
)


def test_model_forward_shape() -> None:
    """MacroPolicyNet must produce (batch_size, 35) output tensors."""
    model = MacroPolicyNet()
    dummy_input = torch.randn(8, 1706)
    out = model(dummy_input)
    assert out.shape == (8, 35)


def test_compute_loss_backward() -> None:
    """Compound loss must compute valid scalar and propagate gradients."""
    model = MacroPolicyNet()
    x = torch.randn(4, 1706)
    logits = model(x)

    targets = {
        "crop": torch.tensor([0, 1, 4, 3], dtype=torch.long),
        "crew": torch.tensor([0, 3, 6, 10], dtype=torch.long),
        "livestock": torch.tensor([0, 1, 2, 3], dtype=torch.long),
        "predation": torch.tensor([0, 1, 2, 0], dtype=torch.long),
        "market": torch.tensor(
            [[1.0, 1.0, 1.0, 1.0], [0.8, 1.2, 0.9, 1.1], [1.5, 0.5, 1.0, 1.0], [1.0, 1.0, 1.0, 1.0]],
            dtype=torch.float32,
        ),
    }

    class_weights = torch.ones(5)
    loss, loss_dict = compute_loss(logits, targets, class_weights)

    assert loss.item() > 0.0
    for k in ("crop", "crew", "livestock", "predation", "market", "total"):
        assert k in loss_dict and loss_dict[k] >= 0.0

    loss.backward()
    assert model.fc1.weight.grad is not None
    assert model.fc_out.weight.grad is not None


def test_export_to_npz_matches_runtime_policy(tmp_path: Path) -> None:
    """Exported weights must match src/model/policy.py shapes and produce matching outputs."""
    model = MacroPolicyNet()
    out_file = tmp_path / "test_weights.npz"

    export_to_npz(model, out_file)
    assert out_file.exists()

    with np.load(out_file) as data:
        assert data["w1"].shape == (1706, 256)
        assert data["b1"].shape == (256,)
        assert data["w2"].shape == (256, 128)
        assert data["b2"].shape == (128,)
        assert data["w_out"].shape == (128, 35)
        assert data["b_out"].shape == (35,)

    # Verify forward pass in NumPy matches PyTorch output for the same input
    test_vec = np.random.randn(1, 1706).astype(np.float32)
    with torch.no_grad():
        pt_out = model(torch.from_numpy(test_vec)).numpy()

    # Manual NumPy forward using exported weights
    with np.load(out_file) as d:
        h1 = np.maximum(0.0, np.dot(test_vec, d["w1"]) + d["b1"])
        h2 = np.maximum(0.0, np.dot(h1, d["w2"]) + d["b2"])
        np_out = np.dot(h2, d["w_out"]) + d["b_out"]

    np.testing.assert_allclose(pt_out, np_out, rtol=1e-4, atol=1e-4)


def test_load_or_create_dataset_fallback(tmp_path: Path) -> None:
    """Missing dataset must auto-generate a valid fallback dataset."""
    missing_path = tmp_path / "missing.npz"
    features, targets = load_or_create_dataset(missing_path, fallback_samples=32)

    assert features.shape == (32, 1706)
    assert targets["crop"].shape == (32,)
    assert targets["crew"].shape == (32,)
    assert targets["livestock"].shape == (32,)
    assert targets["predation"].shape == (32,)
    assert targets["market"].shape == (32, 4)
