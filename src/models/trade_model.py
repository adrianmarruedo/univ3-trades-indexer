from __future__ import annotations

from typing import Optional
from typing_extensions import TypeAlias
from datetime import datetime
from pydantic import BaseModel

Hex: TypeAlias = str  # Explicitly note this is a hex value for ETL pipelines to handle
Address: TypeAlias = str


class TradeModel(BaseModel): 
    chain_id: int
    block_num: int
    tx_hash: str
    type: str
    maker: Address
    taker: Address
    amount_0: str  # BigInt as string for precision
    amount_1: str  # BigInt as string for precision
    token_address_0: Address
    token_address_1: Address
    block_time: Optional[datetime]
