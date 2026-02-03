# Simulation Platform

This platform simulates multi-slot ad auctions with sellers, users, budgets, and automated bidding. It uses Celery + Redis for distributed execution.

## HLD

```mermaid
flowchart LR
O[Opportunities Generator] -->|batches| W[Celery Workers]
Sellers[Sellers + Policies] --> W
W --> A[Aggregator]
A --> R[(Parquet/CSV Results)]
A --> M[Metrics CLI]
```

## LLD

```mermaid
flowchart TB
U[UserGenerator] --> F[Scoring]
S[Sellers] --> P[Policies]
F --> A1[Allocator]
P --> A1
A1 --> E[Events]
E --> K[KPIs]
```

## Sequence

```mermaid
sequenceDiagram
participant CLI
participant Celery
participant Worker
participant Aggregator
CLI->>Celery: submit run_block
Celery->>Worker: simulate_block
Worker-->>Celery: sellers, metrics
Celery-->>CLI: results
CLI->>Aggregator: aggregate and write
```

## Tool Choices

Celery orchestrates independent chunks. Redis is the broker and backend to minimize ops. Alternatives like RabbitMQ provide advanced routing; Kafka suits durable logs. Ray/Dask are better for distributed in-memory arrays; here, tasks are IO-light and independent, so Celery+Redis is sufficient.

Config switches: `world.metrics.roas_mode` ∈ {value_over_spend, profit_over_spend}, `world.metrics.rocs_mode` ∈ {revenue_minus_cogs_over_spend, profit_after_cogs_over_spend}, `world.regulation.{min_quality,min_bid,reserve_cpc}`, and `world.slot_multipliers` for slot CTR curves.
