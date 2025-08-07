from __future__ import annotations

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class SwapEventModel(BaseModel):
    """Simplified Uniswap V3 Swap event model that maps directly to Trade schema"""
    
    chain_id: int
    block_num: int
    tx_hash: str
    log_index: int
    
    pool_address: str
    sender: str
    recipient: str
    amount_0: str
    amount_1: str
    token_address_0: str
    token_address_1: str
    trade_type: str  # "BUY" or "SELL"
    
    # Uniswap V3 specific data
    sqrt_price_x96: str
    tick: int
    liquidity: str
    
    # Timing
    block_time: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
