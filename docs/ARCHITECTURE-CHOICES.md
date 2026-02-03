# Architecture Choices and Rationale

## Orchestration
Celery executes independent simulation chunks across workers.

## Broker
Redis is used for low-latency task queueing and as a simple result backend.

## Alternatives
RabbitMQ adds routing and strong delivery semantics with more ops overhead. Kafka is optimized for durable streams rather than task queues. Ray and Dask provide distributed actors and task graphs when you need shared in-memory state.

## Extra Diagrams

```mermaid
flowchart LR
Client[CLI] --> Q[Redis Queue]
Q --> W1[Worker 1]
Q --> W2[Worker 2]
W1 --> A[Aggregator]
W2 --> A
A --> O[(Parquet/CSV)]
```

```mermaid
sequenceDiagram
participant Seller
participant Pacer
participant Auction
participant Mechanism
participant Metrics
Seller->>Pacer: request multiplier
Pacer-->>Seller: multiplier
Seller->>Auction: bid
Auction->>Mechanism: allocate
Mechanism-->>Auction: winners, prices
Auction->>Metrics: log
```