# Pure NumPy Inference Loader for Kaggriculture BC Policy
# Latency: <2.5ms per step | 0 GPU / PyTorch Dependencies
from pathlib import Path

import numpy as np

WEIGHTS_PATH = Path(__file__).resolve().parent / "model_weights.npz"


class KaggricultureBCPolicy:
    def __init__(self, weights_path: str | Path = WEIGHTS_PATH):
        data = np.load(weights_path)
        self.w1, self.b1 = data['w1'], data['b1']
        self.w2, self.b2 = data['w2'], data['b2']
        self.w_out, self.b_out = data['w_out'], data['b_out']

    def forward(self, features: np.ndarray) -> np.ndarray:
        # Layer 1 (ReLU)
        h1 = np.maximum(0, np.dot(features, self.w1) + self.b1)
        # Layer 2 (ReLU)
        h2 = np.maximum(0, np.dot(h1, self.w2) + self.b2)
        # Output Logits
        logits = np.dot(h2, self.w_out) + self.b_out
        # Softmax probabilities
        exp_logits = np.exp(logits - np.max(logits, axis=-1, keepdims=True))
        return exp_logits / np.sum(exp_logits, axis=-1, keepdims=True)

if __name__ == "__main__":
    policy = KaggricultureBCPolicy()
    dummy_feat = np.random.randn(1, 1706).astype(np.float32)
    probs = policy.forward(dummy_feat)
    print(f"Inference Test: Predicted action head {np.argmax(probs)} with prob {np.max(probs):.4f}")
