import os

import pandas as pd
from celery import Celery, group

from ..config import SimConfig
from .engine import aggregate, simulate_block

app = Celery("sim")
app.config_from_object("celeryconfig")


@app.task
def run_block(cfg_json: str, seed: int, offset: int):
    cfg = SimConfig.model_validate_json(cfg_json)
    s, m = simulate_block(cfg, seed, offset)
    return s.to_dict(orient="list"), m.to_dict(orient="list")


def run_distributed(cfg: SimConfig, run_id: str):
    tasks = []
    total = cfg.world.opportunities
    bs = cfg.world.batch_size
    blocks = (total + bs - 1) // bs
    for b in range(blocks):
        off = b * bs
        tasks.append(run_block.s(cfg.model_dump_json(), cfg.world.start_ts + b, off))
    g = group(tasks)
    res = g.apply_async()
    out = res.get()
    sellers = []
    metrics = []
    for sd, md in out:
        sellers.append(pd.DataFrame(sd))
        metrics.append(pd.DataFrame(md))
    sf, agg = aggregate(list(zip(sellers, metrics)))
    base = f"runs/{run_id}"
    os.makedirs(base, exist_ok=True)
    sf.to_parquet(f"{base}/sellers.parquet", index=False)
    agg.to_parquet(f"{base}/metrics.parquet", index=False)
    sf.to_csv(f"{base}/sellers.csv", index=False)
    agg.to_csv(f"{base}/metrics.csv", index=False)
    return f"{base}/metrics.csv"
