from sqlalchemy import Column
from sqlalchemy.types import Integer, String, DateTime, DECIMAL
from sqlalchemy.sql import func

from ... import Base


class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True)
    chain_id = Column(Integer, nullable=False)
    block_num = Column(Integer, nullable=False)
    tx_hash = Column(String(255), nullable=False)
    log_index = Column(Integer, nullable=False)
    
    pool_address = Column(String(255), nullable=False)
    sender = Column(String(255), nullable=False)
    recipient = Column(String(255), nullable=False)
    amount_0 = Column(DECIMAL(54, 18), nullable=False)
    amount_1 = Column(DECIMAL(54, 18), nullable=False)
    trade_type = Column(String(10), nullable=False)
    token_address_0 = Column(String(255), nullable=False)
    token_address_1 = Column(String(255), nullable=False)
    
    block_time = Column(DateTime)
    created_at = Column(DateTime, server_default=func.current_timestamp())
    updated_at = Column(
        DateTime,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )