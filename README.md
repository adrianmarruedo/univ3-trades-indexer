# Uniswap V3 Trades Indexer

A real-time event-driven data pipeline that indexes all trades from the Uniswap V3 USDC/ETH 0.05% pool (0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640) using Kafka for event streaming and Postgres for data storage.

## Architecture

```
┌─────────────────┐    ┌──────────────┐    ┌─────────────────┐    ┌──────────────┐
│   Web3 Event    │───▶│    Kafka     │───▶│  Trade DB       │───▶│  Postgres    │
│   Listener      │    │   Message    │    │   Writter       │    │   Database   │
│  (Component 1)  │    │    Queue     │    │  (Component 2)  │    │              │
└─────────────────┘    └──────────────┘    └─────────────────┘    └──────────────┘
         │                       │                    │                     │
         │                       │                    │                     │
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

### 2. Trade Processor Service (`src/services/trade_processor.py`)
- Consumes trade events from Kafka (topic `uniswap-v3-trades`)
- Processes and validates trade data using pydantic models and sqlalchemy ORM
- Saves processed trades to Postgres database

### 3. Kafka
- Consumers will be grouped under `trade-processor` group id
- We are currently using one topic (`uniswap-v3-trades`) and no partition. We could expand this to for example using topic `trades`. This would allow us to have different consumers for different events or general purposes (like txs, logs, etc). We could have a component for storing `logs` in the database subscribed to the `logs` topic, totally parallel to the other services.
- We use `auto_offset_reset` set to `earliest` to ensure we don't miss any events

### System upgradability:
- The system is prepared to handle multiple pools for Uniswap V3. `EventListenerService` can be instantiated using pool_address, token_address_0, token_address_1, decimals_0, decimals_1. 
- To listen to more events from the pool, we should add those extra topics to the `constants.evm` file. Then, proceed to implement the parsing in `src/parsers/uniswap_v3_parser.py`.
- The project has been structured so we can fit more Parsers in `src/parsers/` with the idea of using a Parser interface. 

### Scalability:
- The system can scale horizontaly by increasing the number of trade processor services. This might be needed if we expand on the amount of pools/protocols that we are indexing.
- Even if I made the `EventListenerService` horizontally scalable, I would NOT scale the event listener service horizontally in a real case. Instead, I would keep it minimal and general to listen to the SWAP topic of all pools, parse them, and then filter out the ones that we are interested in. Then, send it to the trade processor service.

### Important notes:
- The system is prepared to handle **reorgs**, but it is not a priority to handle them. Reorgs will be considerable when dealing with real time ethereum logs.

### Possible Improvements:
- Use poetry to better handling dependencies.
- For some pieces of data like token_addresses (0 and 1) and decimals, we will need another system to fetch those and store them. 
- Reorg handling.
- Implement different providers & Implement a retry backup strategy when the main provider fails.
- Add indexes and constrains to the database. Better PK creation. Duplication proof.


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
