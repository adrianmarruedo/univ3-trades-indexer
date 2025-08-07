import logging
from typing import Optional

from web3 import Web3
from eth_abi import decode

from src.models import LogModel, SwapEventModel, TradeModel
from src.constants.evm import UNISWAP_V3_SWAP_TOPIC


logger = logging.getLogger(__name__)


class UniswapV3Parser:
    """Parser for Uniswap V3 Swap events"""
    
    def __init__(self, pool_address: str, token_address_0: str, token_address_1: str):
        self.web3 = Web3()
        self.pool_address = pool_address
        self.token_address_0 = token_address_0
        self.token_address_1 = token_address_1
    
    def parse_swap_log(self, log: LogModel) -> Optional[SwapEventModel]:
        """Parse a raw log into a SwapEventModel ready for database insertion"""
        try:
            # Verify this is a Swap event
            if not log.topics or log.topics[0] != UNISWAP_V3_SWAP_TOPIC:
                logger.warning(f"Log is not a Uniswap V3 Swap event: {log.topic}")
                return None
            
            # Extract indexed parameters (sender, recipient)
            if len(log.topics) < 3:
                logger.error(f"Insufficient topics for Swap event: {len(log.topics)}")
                return None
                
            sender = self._decode_address(log.topics[1])
            recipient = self._decode_address(log.topics[2])
            
            # Decode non-indexed parameters from data
            try:
                decoded_data = decode(
                    ['int256', 'int256', 'uint160', 'uint128', 'int24'],
                    bytes.fromhex(log.data[2:])  # Remove '0x' prefix
                )
                
                amount0, amount1, sqrt_price_x96, liquidity, tick = decoded_data
                
            except Exception as e:
                logger.error(f"Failed to decode swap event data: {e}")
                return None
            
            trade_type = "BUY" if amount0 < 0 else "SELL"  
            
            swap_event = SwapEventModel(
                chain_id=log.chain_id,
                block_num=log.block_num,
                tx_hash=log.transaction_hash,
                log_index=log.log_index,
                pool_address=self.pool_address,
                sender=sender,
                recipient=recipient,
                amount_0=str(amount0),
                amount_1=str(amount1),
                trade_type=trade_type,
                sqrt_price_x96=str(sqrt_price_x96),
                tick=tick,
                liquidity=str(liquidity),
                block_time=log.block_time,
                token_address_0=self.token_address_0,
                token_address_1=self.token_address_1
            )
            
            return swap_event
            
        except Exception as e:
            logger.error(f"Error parsing swap log: {e}")
            return None
    
    def conform_trades(self, swap_event: SwapEventModel) -> TradeModel:
        """Convert SwapEventModel to TradeModel for final trade representation"""
        try:
            # Keep amounts as strings for BigInt precision and JSON serialization
            trade = TradeModel(
                chain_id=swap_event.chain_id,
                block_num=swap_event.block_num,
                tx_hash=swap_event.tx_hash,
                type=swap_event.trade_type,  
                maker=swap_event.sender,     
                taker=swap_event.recipient,  
                amount_0=swap_event.amount_0,  # Keep as string
                amount_1=swap_event.amount_1,  # Keep as string
                token_address_0=swap_event.token_address_0,
                token_address_1=swap_event.token_address_1,
                block_time=swap_event.block_time
            )
            
            return trade
            
        except Exception as e:
            logger.error(f"Error conforming swap event to trade: {e}")
            raise

    
    def _decode_address(self, topic: str) -> str:
        """Decode an address from a topic (32-byte hex string)"""
        # Remove '0x' prefix and take last 40 characters (20 bytes = address)
        address_hex = topic[2:] if topic.startswith('0x') else topic
        address = '0x' + address_hex[-40:].lower()
        return address
