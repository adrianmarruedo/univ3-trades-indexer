# Uniswap V3 Trades Indexer

A real-time event-driven data pipeline that indexes all trades from the Uniswap V3 USDC/ETH 0.05% pool (0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640) using Kafka for event streaming and Postgres for data storage.

## Architecture

```
┌─────────────────┐    ┌──────────────┐    ┌─────────────────┐    ┌──────────────┐
│   Web3 Event    │───▶│    Kafka     │───▶│  Trade DB       │───▶│  Postgres    │
│   Listener      │    │   Message    │    │   Writter       │    │   Database   │
│  (Component 1)  │    │    Queue     │    │  (Component 2)  │    │              │
└─────────────────┘    └──────────────┘    └─────────────────┘    └──────────────┘
         │                       │                    │                       │
         │                       │                    │                       │
    ┌────▼────┐              ┌───▼───┐           ┌────▼───-──┐           ┌────▼────┐
    │ Alchemy |              |       |           |           |           |         |
    | Uniswap │              │ Event │           │ sqlalchemy│           │ Trade   │
    │ V3 Pool │              │ Stream│           │ ORM       │           │ Records │
    │ Events  │              │       │           │           │           │         │
    └─────────┘              └───────┘           └───────────┘           └─────────┘
```

## Components

### 1. Event Listener Service (`src/services/event_listener.py`)
- Subscribes to Uniswap V3 pool for `Swap` events using Web3 (alchemy rpc provider)
- Parses raw blockchain logs into structured events using pydantic models. This way we ensure runtime type validation
- Publishes events to Kafka message queue (topic `uniswap-v3-trades`)
- Handles reconnections and error recovery
- The first implementation was using eth_getLogs and polling every second. Later, I developed the websocket implementation.

### 2. Trade Processor Service (`src/services/trade_processor.py`)
- Consumes trade events from Kafka (topic `uniswap-v3-trades`)
- Processes and validates trade data using pydantic models and sqlalchemy ORM
- Saves processed trades to Postgres database

### 3. Kafka
- Consumers will be grouped under `trade-processor` group id
- We are currently using one topic (`uniswap-v3-trades`) and no partition. We could expand this to for example using topic `trades`. This would allow us to have different consumers for different events or general purposes (like txs, logs, etc). We could have a component for storing `logs` in the database subscribed to the `logs` topic, totally parallel to the other services.
- We use `auto_offset_reset` set to `earliest` to ensure we don't miss any events


## Final Data Model

### Trades Table Schema

```sql
CREATE TABLE trades (
    id                SERIAL PRIMARY KEY,
    chain_id          INTEGER NOT NULL,
    block_num         INTEGER NOT NULL,
    tx_hash           VARCHAR(255) NOT NULL,
    log_index         INTEGER NOT NULL,
    
    pool_address      VARCHAR(255) NOT NULL,
    sender            VARCHAR(255) NOT NULL,
    recipient         VARCHAR(255) NOT NULL,
    amount_0          DECIMAL(54, 18) NOT NULL,  -- Token0 amount (BigInt precision)
    amount_1          DECIMAL(54, 18) NOT NULL,  -- Token1 amount (BigInt precision)
    trade_type        VARCHAR(10) NOT NULL,      -- 'BUY' or 'SELL'
    token_address_0   VARCHAR(255) NOT NULL,     -- Token0 contract address
    token_address_1   VARCHAR(255) NOT NULL,     -- Token1 contract address
    
    block_time        TIMESTAMP,
    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```


## Quick Start

### Prerequisites

- Docker and Docker Compose
- Alchemy API key

### 1. Clone and Setup Environment

```bash
cp .env_template .env
```

### 2. Configure Environment Variables

Edit `.env` file with your settings

### 3. Start the Pipeline

```bash
# Start all services with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f event-listener
docker-compose logs -f trade-processor
```

### 4. Verify Operation

```bash
# Connect to Postgres and verify data
docker-compose exec postgres psql -U postgres -d trades_indexer

SELECT * FROM trades ORDER BY created_at DESC LIMIT 10;
```

## Development

Requirements
- Python 3.11


### Local Development Setup

```bash
# Install Python dependencies
pip install -r requirements.txt

# Start infrastructure only
docker-compose up -d zookeeper kafka postgres

# Run services locally
python app_pub.py    # Event listener service
python app_sub.py    # Trade processor service
```

### Troubleshooting

If you already have postgres running on your machine and using the same port as the one specified in the .env file, you can change the port in the .env file or stop the postgres service.
