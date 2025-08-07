import logging
import signal
from typing import Dict, Any

from config import settings
from src.kafka.consumer import TradeEventConsumer
from src.models import TradeModel
from src.db import Base
from src.db.db_utils import create_tables
from src.db.schemas.trade.trades_intake import save_trade_to_db

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TradeProcessorService:
    """Service that consumes trade events from Kafka and saves to database"""
    
    def __init__(self):
        self.running = False
        self.kafka_consumer = None
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
    
    def initialize(self):
        """Initialize database and Kafka consumer"""
        try:
            # Create tables if they don't exist using existing utility
            create_tables(metadata=Base.metadata) # TODO: Think of deleting
            
            self.kafka_consumer = TradeEventConsumer(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                group_id="trade-processor"
            )
            
            # Subscribe to trades topic
            self.kafka_consumer.subscribe(["uniswap-v3-trades"])
            
            logger.info("Trade processor service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize trade processor service: {e}")
            raise
    
    def start_processing(self):
        """Start processing trade events from Kafka"""
        self.running = True
        logger.info("Starting trade event processing...")
        
        try:
            self.kafka_consumer.consume_messages(self._process_trade_message)
            
        except Exception as e:
            logger.error(f"Fatal error in trade processing: {e}")
            raise
        finally:
            logger.info("Trade processing stopped")
    
    def _process_trade_message(self, trade_data: Dict[str, Any]):
        """Process a single trade message from Kafka"""
        try:
            # Convert dict back to TradeModel
            trade = TradeModel(**trade_data)
            
            # Save to database using existing utility function
            save_trade_to_db(trade)
            
            logger.info(f"Processed and saved trade: {trade.tx_hash}")
            
        except Exception as e:
            logger.error(f"Error processing trade message: {e}")
    
    def cleanup(self):
        """Cleanup resources"""
        logger.info("Cleaning up trade processor service...")
        
        if self.kafka_consumer:
            self.kafka_consumer.close()
        
        logger.info("Trade processor service cleanup completed")
