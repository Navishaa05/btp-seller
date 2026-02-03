# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Setup
```bash
# Create virtualenv and install dependencies
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

### Redis Setup
Start Redis (required for distributed execution):
```bash
# Using Docker
docker compose up -d redis

# Or on macOS with Homebrew
brew services start redis
```

### Running Simulations
```bash
# Start Celery worker for distributed mode
celery -A auction_sim.simulation.tasks worker --loglevel INFO

# Run simulation (single-process)
python -m auction_sim.cli run --config configs/example.json

# Run simulation (distributed with Celery)
python -m auction_sim.cli run --config configs/example.json --distributed

# Or using the installed script
auction-sim run --config configs/example.json
```

### Output Inspection
Results are written to `runs/<timestamp>/`:
- `sellers.parquet` / `sellers.csv` - per-seller KPIs (spend, clicks, conversions, revenue, ROAS, ROCS)
- `metrics.parquet` / `metrics.csv` - run-level aggregates (platform revenue, social welfare, user experience)

## Architecture Overview

### Core Simulation Flow
The platform simulates multi-slot ad auctions with sellers, users, budgets, and automated bidding strategies.

**High-level execution:**
1. CLI (`cli.py`) loads config and orchestrates execution
2. Opportunities are divided into batches (configurable via `world.batch_size`)
3. Each batch is simulated by `simulate_block()` in `simulation/engine.py`
4. In distributed mode, batches are submitted as Celery tasks to Redis queue
5. Results are aggregated and written to Parquet/CSV

**Key simulation loop (per opportunity):**
1. User features generated via `UserGenerator` with diurnal patterns
2. Sellers compute bids using either `RudimentaryPolicy` or `AutoBidPolicy`
3. `Regulator` screens bids/quality scores against min_quality, min_bid thresholds
4. Auction mechanism (GSP/VCG/First-Price) allocates slots and computes prices
5. Stochastic clicks/conversions simulated based on CTR/CVR predictions
6. Seller budgets decremented, metrics accumulated

### Module Structure

**`config.py`**: Pydantic models for configuration
- `SimConfig` - top-level config with `world` and `sellers`
- `WorldConfig` - environment settings (opportunities, slots, mechanism, regulation, metrics modes)
- `SellerConfig` - per-seller budget, value_per_conversion, policy type, COGS ratio

**`simulation/engine.py`**: Core simulation logic
- `simulate_block(cfg, seed, start_offset)` - simulates a batch of opportunities, returns seller DataFrame and metrics DataFrame
- `aggregate(results)` - merges results from multiple blocks

**`simulation/tasks.py`**: Celery distributed execution
- `run_block` - Celery task wrapper for `simulate_block()`
- `run_distributed()` - splits work into Celery tasks, aggregates results

**`auction/mechanisms.py`**: Allocation and pricing
- `allocate(bids, qs, k)` - ranks by score (bid × quality), selects top-k
- `prices_gsp()` - Generalized Second Price
- `prices_vcg()` - Vickrey-Clarke-Groves
- `prices_first_price()` - First-price auction

**`auction/regulation.py`**: Quality/bid screening
- `Regulator.screen(bids, qs)` - filters out bids/ads below min_quality, min_bid, reserve_cpc thresholds

**`market/sellers.py`**: Seller and bidding policy implementations
- `Seller` dataclass - stores seller config and embedding
- `RudimentaryPolicy` - simple bid = value_per_conversion × base_bid_shading × cvr
- `AutoBidPolicy` - adaptive bidding with `PacingController` for budget management
- `PacingController` - adjusts bid multiplier based on spend vs. budget pacing target

**`market/users.py`**: User/opportunity generation
- `UserGenerator` - creates user embeddings with diurnal traffic patterns and noise

**`utils/features.py`**: Feature engineering utilities (embeddings, sigmoid, scoring functions)

**`analysis.py`**: Post-simulation analysis utilities

### Key Configuration Switches

Located in JSON config files (`configs/`):

**Auction Mechanisms** (`world.mechanism`):
- `"gsp"` - Generalized Second Price (default)
- `"vcg"` - Vickrey-Clarke-Groves
- `"first_price"` - First-price auction

**Metrics Modes** (`world.metrics`):
- `roas_mode`: `"value_over_spend"` (default) or `"profit_over_spend"`
- `rocs_mode`: `"revenue_minus_cogs_over_spend"` (default) or `"profit_after_cogs_over_spend"`

**Regulation** (`world.regulation`):
- `min_quality`: minimum quality score threshold
- `min_bid`: minimum bid threshold
- `reserve_cpc`: reserve price per click

**Slot Configuration** (`world.slot_multipliers`):
- Array of CTR multipliers for each slot position (e.g., `[1.0, 0.7, 0.5]`)

**Seller Policies** (`sellers[].policy`):
- `"rudimentary"` - static bid shading
- `"auto"` - adaptive bidding with budget pacing

### Celery Configuration

Located in `celeryconfig.py` at repo root:
- Broker/backend default to `redis://localhost:6379/0`
- Override via `CELERY_BROKER_URL` and `CELERY_RESULT_BACKEND` env vars
- Task queue: `"sim"`
- Serialization: JSON

### Important Implementation Details

**Randomness and Reproducibility:**
- Each block uses a deterministic seed based on `world.start_ts` + offset
- User generation, seller embeddings, click/conversion events all seeded independently

**Quality Score Normalization:**
- Quality scores computed as CTR normalized by max CTR in opportunity
- Used in auction scoring: score = bid × quality

**Budget Enforcement:**
- Budgets are daily limits (`daily_budget`)
- Bids set to 0 when `remaining_budget <= 0`
- AutoBidPolicy uses PacingController to smooth spend over time horizon

**Metrics Calculation:**
- ROAS/ROCS computed per seller after aggregation
- Platform revenue = sum of all payments
- Social welfare = sum of all conversion values
- User experience = average slot CTR across opportunities
