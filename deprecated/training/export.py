"""Weight exporter and parity verifier for PyTorch models to NumPy SIMD weights."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import torch
import torch.nn as nn

__all__ = ["export_torch_to_npz", "verify_parity"]


def export_torch_to_npz(model: nn.Module, output_path: Path | str) -> None:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sd = model.state_dict()
    np.savez_compressed(
        str(output_path),
        w1=sd["fc1.weight"].detach().cpu().numpy().T.astype(np.float32),
        b1=sd["fc1.bias"].detach().cpu().numpy().astype(np.float32),
        w2=sd["fc2.weight"].detach().cpu().numpy().T.astype(np.float32),
        b2=sd["fc2.bias"].detach().cpu().numpy().astype(np.float32),
        w_out=sd["fc_out.weight"].detach().cpu().numpy().T.astype(np.float32),
        b_out=sd["fc_out.bias"].detach().cpu().numpy().astype(np.float32),
    )


def verify_parity(
    model: nn.Module,
    npz_path: Path | str,
    n_samples: int = 100,
    seed: int = 42,
) -> float:
    rng = np.random.default_rng(seed)
    test_inputs = rng.standard_normal((n_samples, 1706), dtype=np.float32)

    model.eval()
    with torch.no_grad():
        x_tensor = torch.from_numpy(test_inputs)
        torch_logits = model(x_tensor).cpu().numpy()

    data = np.load(str(npz_path))
    w1, b1 = data["w1"], data["b1"]
    w2, b2 = data["w2"], data["b2"]
    w_out, b_out = data["w_out"], data["b_out"]

    h1 = np.maximum(0.0, np.dot(test_inputs, w1) + b1)
    h2 = np.maximum(0.0, np.dot(h1, w2) + b2)
    numpy_logits = np.dot(h2, w_out) + b_out

    max_diff = float(np.max(np.abs(torch_logits - numpy_logits)))
    return max_diff
