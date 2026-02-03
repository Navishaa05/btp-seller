from typing import List

from pydantic import BaseModel, Field


class RegulationConfig(BaseModel):
    min_quality: float = 0.0
    min_bid: float = 0.0
    reserve_cpc: float = 0.0


class MetricsConfig(BaseModel):
    roas_mode: str = "value_over_spend"
    rocs_mode: str = "revenue_minus_cogs_over_spend"


class SellerConfig(BaseModel):
    id: str
    brand: str = "generic"
    daily_budget: float
    value_per_conversion: float
    cogs_ratio: float = 0.5
    base_bid_shading: float = 0.8
    policy: str = "auto"
    seed: int = 0


class WorldConfig(BaseModel):
    start_ts: int
    horizon_hours: int
    opportunities: int
    batch_size: int = 100000
    slots: int = 3
    slot_multipliers: List[float] = Field(default_factory=lambda: [1.0, 0.7, 0.5])
    mechanism: str = "gsp"
    embedding_dim: int = 16
    base_ctr: float = 0.02
    base_cvr: float = 0.02
    diurnal_amplitude: float = 0.2
    noise_std: float = 0.1
    regulation: RegulationConfig = RegulationConfig()
    metrics: MetricsConfig = MetricsConfig()


class SimConfig(BaseModel):
    world: WorldConfig
    sellers: List[SellerConfig]
