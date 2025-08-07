import logging
import sys

from src.services.trade_processor import TradeProcessorService

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point for the trade processor service"""
    service = TradeProcessorService()
    
    try:
        service.initialize()
        service.start_processing()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Service error: {e}")
        sys.exit(1)
    finally:
        service.cleanup()


if __name__ == "__main__":
    main()
