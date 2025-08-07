import asyncio
import logging
import sys

from src.constants.evm import USDC_ETH_POOL_ADDRESS, USDC, WETH
from src.services.event_listener import EventListenerService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Main entry point for the event listener service"""
    service = EventListenerService(
        pool_address=USDC_ETH_POOL_ADDRESS,
        token_address_0=USDC,
        token_address_1=WETH
    )
    
    try:
        await service.initialize()
        await service.start_listening()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Service error: {e}")
        sys.exit(1)
    finally:
        await service.cleanup()


if __name__ == "__main__":
    asyncio.run(main())