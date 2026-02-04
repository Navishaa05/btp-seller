import os
import pandas as pd
from celery import Celery, group
from ..config import SimConfig
from .engine import aggregate, simulate_block

app = Celery("sim")
app.config_from_object("celeryconfig")

@app.task
def run_block(cfg_json: str, seed: int, offset: int):
    # This print helps us verify the worker is updated
    print("DEBUG: Running UPDATED run_block with history tracking!")
    cfg = SimConfig.model_validate_json(cfg_json)
    s, m, h = simulate_block(cfg, seed, offset)
    return s.to_dict(orient="list"), m.to_dict(orient="list"), h.to_dict(orient="list")

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
    
    sellers_dfs, metrics_dfs, history_dfs = [], [], []
    
    # --- FIXED LINE 33 ---
    for sd, md, hd in out: 
        sellers_dfs.append(pd.DataFrame(sd))
        metrics_dfs.append(pd.DataFrame(md))
        history_dfs.append(pd.DataFrame(hd))
    
    # Aggregate results
    sf, agg = aggregate(list(zip(sellers_dfs, metrics_dfs, history_dfs)))
    hf = pd.concat(history_dfs, ignore_index=True)

    base = f"runs/{run_id}"
    os.makedirs(base, exist_ok=True)
    
    # Save files
    sf.to_csv(f"{base}/sellers.csv", index=False)
    sf.to_parquet(f"{base}/sellers.parquet", index=False) # Restore this
    
    agg.to_csv(f"{base}/metrics.csv", index=False)
    agg.to_parquet(f"{base}/metrics.parquet", index=False) # Restore this
    
    hf.to_csv(f"{base}/history.csv", index=False)
    
    print(f"Success! All files (CSV/Parquet/History) saved to {base}/")
    return f"{base}/metrics.csv"