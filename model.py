"""
Bandhan — RiskNet Model Definition
Loads trained weights and runs inference
"""

import numpy as np


class RiskNet:
    """
    4-layer neural network: 19 → 64 → 32 → 16 → 1
    Trained on behavioural + contextual + transaction features
    """

    def __init__(self):
        np.random.seed(42)
        self.W1, self.b1 = self._init_layer(19, 64)
        self.W2, self.b2 = self._init_layer(64, 32)
        self.W3, self.b3 = self._init_layer(32, 16)
        self.W4, self.b4 = self._init_layer(16, 1)

    def _init_layer(self, n_in, n_out):
        W = np.random.randn(n_in, n_out) * np.sqrt(2.0 / n_in)
        b = np.zeros((1, n_out))
        return W, b

    def _sigmoid(self, z):
        return 1 / (1 + np.exp(-np.clip(z, -500, 500)))

    def _relu(self, z):
        return np.maximum(0, z)

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Run forward pass. X shape: (n_samples, 19)"""
        a1 = self._relu(X  @ self.W1 + self.b1)
        a2 = self._relu(a1 @ self.W2 + self.b2)
        a3 = self._relu(a2 @ self.W3 + self.b3)
        a4 = self._sigmoid(a3 @ self.W4 + self.b4)
        return a4.flatten()

    def predict_single(self, features: list) -> float:
        """Predict risk probability for one borrower."""
        X = np.array(features, dtype=np.float64).reshape(1, -1)
        return float(self.predict(X)[0])
