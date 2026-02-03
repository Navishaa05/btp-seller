import numpy as np

from auction_sim.utils import features


class UserGenerator:
    def __init__(
        self, d: int, base_ctr: float, base_cvr: float, amp: float, noise: float, seed: int
    ):
        self.d = d
        self.base_ctr = base_ctr
        self.base_cvr = base_cvr
        self.amp = amp
        self.noise = noise
        self.r = np.random.default_rng(seed)

    def batch(self, n: int, t0: int, horizon_hours: int):
        u = features.unit_embeddings(self.r, n, self.d)
        ts = self.r.integers(t0, t0 + horizon_hours * 3600, size=n)
        h = ((ts // 3600) % 24).astype(np.int32)
        diurnal = 1.0 + self.amp * np.sin(2 * np.pi * h / 24.0)
        return u, ts, diurnal
