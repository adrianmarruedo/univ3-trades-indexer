import logging
import sys

from src.services.trade_processor import TradeProcessorService
from src.db import Base
from src.db.db_utils import create_tables

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point for the trade processor service"""
    try:
        # Create database tables if they don't exist
        create_tables(metadata=Base.metadata)
        logger.info("Database tables ensured")
        
        service = TradeProcessorService()
        service.initialize()
        service.start_processing()
        
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Service error: {e}")
        sys.exit(1)
    finally:
        service.cleanup()


if __name__ == "__main__":
    main()
