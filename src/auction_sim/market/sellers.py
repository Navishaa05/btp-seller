from dataclasses import dataclass

import numpy as np


# -----------------------------
# Campaign abstraction
# -----------------------------
@dataclass
class Campaign:
    name: str
    daily_budget: float
    base_bid: float
    spent: float = 0.0

    def remaining_budget(self):
        return max(0.0, self.daily_budget - self.spent)

    def pacing_multiplier(self, elapsed_frac):
        """Simple proportional pacing"""
        target_spend = self.daily_budget * elapsed_frac
        if self.spent > target_spend:
            return 0.7
        return 1.1


# -----------------------------
# Seller
# -----------------------------
@dataclass
class Seller:
    id: str
    brand: str
    daily_budget: float
    value_per_conversion: float
    cogs_ratio: float
    base_bid_shading: float
    policy: str
    seed: int
    d: int
    ad_vec: np.ndarray

    spend: float = 0.0
    clicks: int = 0
    conv: int = 0
    revenue: float = 0.0

    def __post_init__(self):
        # default single campaign
        self.campaigns = [
            Campaign(
                name="default",
                daily_budget=self.daily_budget,
                base_bid=self.base_bid_shading * self.value_per_conversion,
            )
        ]

    def bid(self, p_ctr, p_cvr, elapsed_frac):
        if not self.campaigns:
            return 0.0, None

        campaign = self.campaigns[0]  # single-campaign for now

        if campaign.remaining_budget() <= 0:
            return 0.0, None

        v = self.value_per_conversion * p_cvr
        bid = self.base_bid_shading * v
        return bid, campaign

    def charge(self, price, campaign):
        self.spend += price
        if campaign is not None:
            campaign.spent += price


# -----------------------------
# Seller factory
# -----------------------------
def make_sellers(cfg, d, seed):
    r = np.random.default_rng(seed)
    out = []

    for sc in cfg.sellers:
        vec = r.normal(0, 1, size=d)
        vec /= np.linalg.norm(vec) + 1e-8

        out.append(
            Seller(
                id=sc.id,
                brand=sc.brand,
                daily_budget=sc.daily_budget,
                value_per_conversion=sc.value_per_conversion,
                cogs_ratio=sc.cogs_ratio,
                base_bid_shading=sc.base_bid_shading,
                policy=sc.policy,
                seed=sc.seed,
                d=d,
                ad_vec=vec,
            )
        )
    return out
