import os
import time

import click

from auction_sim.config import SimConfig
from auction_sim.simulation.engine import aggregate, simulate_block
from auction_sim.simulation.tasks import run_distributed


@click.group()
def cli():
    pass


@cli.command()
@click.option("--config", type=click.Path(exists=True), required=True)
@click.option("--distributed", is_flag=True, default=False)
def run(config, distributed):
    with open(config) as f:
        cfg = SimConfig.model_validate_json(f.read())
    run_id = str(int(time.time()))
    if distributed:
        res = run_distributed(cfg, run_id)
        click.echo(res)
    else:
        results = []
        seed = cfg.world.start_ts
        for i in range(0, cfg.world.opportunities, cfg.world.batch_size):
            s, m = simulate_block(cfg, seed + i, i)
            results.append((s, m))
        sf, agg = aggregate(results)
        base = f"runs/{run_id}"
        os.makedirs(base, exist_ok=True)
        sf.to_parquet(f"{base}/sellers.parquet", index=False)
        agg.to_parquet(f"{base}/metrics.parquet", index=False)
        sf.to_csv(f"{base}/sellers.csv", index=False)
        agg.to_csv(f"{base}/metrics.csv", index=False)
        click.echo(f"{base}/metrics.csv")


if __name__ == "__main__":
    cli()
