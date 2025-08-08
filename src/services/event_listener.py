import asyncio
import logging
import signal
from typing import Dict, Any

from config import settings
from src.kafka.producer import TradeEventProducer
from src.providers.alchemy import AlchemyProvider
from src.parsers.uniswap_v3_parser import UniswapV3Parser
from src.constants.evm import UNISWAP_V3_SWAP_TOPIC, CHAIN_ID, DEFAULT_DECIMALS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


KAFKA_TOPIC_TRADES = "uniswap-v3-trades"


class EventListenerService:
    """Service that listens to Uniswap V3 pool events and publishes to Kafka"""
    
    def __init__(
        self, 
        pool_address: str, 
        token_address_0: str, 
        token_address_1: str, 
        decimals_0: int = DEFAULT_DECIMALS, 
        decimals_1: int = DEFAULT_DECIMALS
    ):
        self.running = False
        self.kafka_producer = None
        self.parser = None
        self.provider = None
        self.pool_address = pool_address
        self.token_address_0 = token_address_0
        self.token_address_1 = token_address_1
        self.decimals_0 = decimals_0
        self.decimals_1 = decimals_1
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
    
    async def initialize(self):
        """Initialize Alchemy provider and Kafka producer"""
        try:
            # Initialize Alchemy provider (handles Web3 connection internally)
            self.provider = AlchemyProvider(
                chain_id=CHAIN_ID,
                host=settings.PROVIDER_URL,
                websocket=settings.PROVIDER_WEBSOCKET,
                api_key=settings.PROVIDER_KEY
            )
            
            logger.info(f"Connected to Web3 provider. Latest block: {self.provider.latest_block_number()}")
            
            # Initialize parser with token addresses
            self.parser = UniswapV3Parser(
                pool_address=self.pool_address,
                token_address_0=self.token_address_0,
                token_address_1=self.token_address_1,
                decimals_0=self.decimals_0,
                decimals_1=self.decimals_1
            )
            
            # Initialize Kafka producer
            self.kafka_producer = TradeEventProducer(settings.KAFKA_BOOTSTRAP_SERVERS)
            
            logger.info("Event listener service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize event listener service: {e}")
            raise
    
    async def start_listening(self):
        """Start listening for Uniswap V3 swap events via WebSocket"""
        self.running = True
        
        try:
            logger.info("Starting real-time WebSocket event listening...")
            
            # Use WebSocket for real-time event streaming
            async for log_entry in self.provider.listen_for_events_realtime(
                contract_address=self.pool_address,
                topics=[UNISWAP_V3_SWAP_TOPIC]
            ):
                if not self.running: # Emergency stop
                    logger.info("Stopping event listener...")
                    break
                    
                try:
                    await self._process_log_entry(log_entry)
                except Exception as e:
                    logger.error(f"Error processing log entry: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error in WebSocket event listening: {e}")
        finally:
            if self.kafka_producer:
                self.kafka_producer.close()
    
    async def polling_fallback(self):
        """Polling fetching logs every 1 second. Keeping this just in case"""
        try:
            # Create event filter for Swap events
            event_filter = self.provider.create_event_filter(
                contract_address=self.provider.checksum_address(self.pool_address),
                topics=[UNISWAP_V3_SWAP_TOPIC]
            )
            
            logger.info("Event filter created, using polling...")
            
            while self.running:
                try:
                    new_entries = event_filter.get_new_entries()
                    for log_entry in new_entries:
                        await self._process_log_entry(log_entry)
                    
                    # Sleep briefly to avoid overwhelming the provider
                    await asyncio.sleep(1) 
                    
                except Exception as e:
                    logger.error(f"Error processing events in fallback mode: {e}")
                    await asyncio.sleep(5)  # Wait before retrying
                    
        except Exception as e:
            logger.error(f"Error in polling fallback: {e}")
            raise
    
    async def _process_log_entry(self, log_entry):
        """Process a single log entry and send to Kafka"""
        try:
            swap_event = self.parser.parse_swap_log(log_entry)
            
            if swap_event:
                # Convert swap event to trade using conform_trades method
                trade = self.parser.conform_trades(swap_event)
                
                # Send trade (not swap event) to Kafka
                trade_data = trade.dict()
                message_key = trade.tx_hash
                
                success = self.kafka_producer.send_trade_event(
                    topic=KAFKA_TOPIC_TRADES,
                    trade_data=trade_data,
                    key=message_key
                )
                
                if success:
                    logger.info(f"Sent trade to Kafka: {trade.tx_hash}")
                else:
                    logger.error(f"Failed to send trade to Kafka: {trade.tx_hash}")
            
        except Exception as e:
            logger.error(f"Error processing log entry: {e}")
    
    async def cleanup(self):
        """Cleanup resources"""
        logger.info("Cleaning up event listener service...")
        
        if self.kafka_producer:
            self.kafka_producer.close()
        
        logger.info("Event listener service cleanup completed")

