import numpy as np


def unit_embeddings(r, n, d):
    x = r.normal(0, 1, size=(n, d))
    x /= np.linalg.norm(x, axis=1, keepdims=True) + 1e-8
    return x


def sigmoid(x):
    return 1 / (1 + np.exp(-x))
