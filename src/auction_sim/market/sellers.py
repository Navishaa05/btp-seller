from dataclasses import dataclass, field
import numpy as np

@dataclass
class Campaign:
    name: str
    daily_budget: float
    base_bid: float
    spent: float = 0.0

    def remaining_budget(self):
        return max(0.0, self.daily_budget - self.spent)

@dataclass
class Seller:
    id: str
    brand: str
    daily_budget: float
    value_per_conversion: float
    cogs_ratio: float
    base_bid_shading: float  # This will now be dynamic
    policy: str              # aggressive, roi_driven, conservative, risk_averse
    seed: int
    d: int
    ad_vec: np.ndarray

    spend: float = 0.0
    clicks: int = 0
    conv: int = 0
    revenue: float = 0.0
    
    # --- New state tracking from your notes ---
    history: list = field(default_factory=list) 

    def __post_init__(self):
        self.campaigns = [
            Campaign(
                name="default",
                daily_budget=self.daily_budget,
                base_bid=self.base_bid_shading * self.value_per_conversion,
            )
        ]

    def bid(self, p_ctr, p_cvr, elapsed_frac):
        campaign = self.campaigns[0]
        if campaign.remaining_budget() <= 0:
            return 0.0, None

        # Valuation v = Value * predicted CVR (as per your notes)
        v = self.value_per_conversion * p_cvr
        
        # Action: Apply the current dynamic bid shading
        bid = self.base_bid_shading * v
        return bid, campaign

    def observe_and_adapt(self, click, conv, price, elapsed_frac):
        # 1. Update Core Cumulative Stats
        self.spend += price
        self.clicks += int(click)
        self.conv += int(conv)
        rev_gain = int(conv) * self.value_per_conversion
        self.revenue += rev_gain
        
        # 2. BUDGET FIX: Update the campaign object so the bid() method knows spend has happened
        if self.campaigns:
            self.campaigns[0].spent += price

        # 3. Strategy Adaptation (Refined Multipliers for 300k Interactions)
        if self.policy == "aggressive":
            # Target spending 5% ahead of clock
            if (self.spend / self.daily_budget) < (elapsed_frac + 0.05):
                self.base_bid_shading *= 1.0001 # Micro-increase
            
        elif self.policy == "roi_driven":
            # Target a ROAS of 4.0
            current_roas = (self.revenue / self.spend) if self.spend > 1.0 else 4.0
            if current_roas < 4.0: 
                self.base_bid_shading *= 0.9999 # Micro-decrease
            else:
                self.base_bid_shading *= 1.00005

        elif self.policy == "conservative":
            # Stay exactly on the schedule
            if (self.spend / self.daily_budget) > elapsed_frac:
                self.base_bid_shading *= 0.9999 
            else:
                self.base_bid_shading *= 1.00002

        elif self.policy == "risk_averse":
            # Penalize bid if click was paid for but no conversion occurred
            if price > 0 and conv == 0:
                self.base_bid_shading *= 0.9999 
            elif conv > 0:
                self.base_bid_shading *= 1.0002

        elif self.policy == "exploratory":
            # Small random fluctuations to discover market efficiency
            noise = np.random.uniform(0.9998, 1.0002)
            self.base_bid_shading *= noise

        # 4. Final Safety Constraints
        self.base_bid_shading = np.clip(self.base_bid_shading, 0.01, 5.0)
        
    def charge(self, price, campaign):
        # This is kept for compatibility with existing engine, 
        # but logic moved to observe_and_adapt
        pass

    # Add this inside the Seller class in sellers.py

    def get_log_snapshot(self, elapsed_frac):
        """Captures the current state for Page 4 Metrics"""
        return {
            "seller_id": self.id,
            "policy": self.policy,
            "elapsed_frac": elapsed_frac,
            "base_bid_shading": self.base_bid_shading,
            "current_spend": self.spend,
            "current_roas": (self.revenue / self.spend) if self.spend > 0 else 0.0,
        }
    
def make_sellers(cfg, d, seed):
    """
    Factory function to create seller objects from the configuration.
    This is required by engine.py to initialize the simulation.
    """
    r = np.random.default_rng(seed)
    out = []

    for sc in cfg.sellers:
        # Generate a random embedding vector for the brand (Page 1 theory)
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