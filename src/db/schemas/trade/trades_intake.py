from __future__ import annotations

import logging
from typing import List, Dict
from decimal import Decimal

from ...db_utils import DBSession
from . import Trade

from src.models import TradeModel


def _trade_model_to_dict(trade: TradeModel) -> Dict:
    """Low overhead pydantic TradeModel to dict"""
    return {
        "chain_id": trade.chain_id,
        "block_num": trade.block_num,
        "tx_hash": trade.tx_hash,
        "log_index": trade.log_index,
        "pool_address": trade.pool_address,
        "sender": trade.sender,
        "recipient": trade.recipient,
        "amount_0": Decimal(int(trade.amount_0) / Decimal(10 ** trade.decimals_0)),
        "amount_1": Decimal(int(trade.amount_1) / Decimal(10 ** trade.decimals_1)),
        "trade_type": trade.type,
        "token_address_0": trade.token_address_0,
        "token_address_1": trade.token_address_1,
        "block_time": trade.block_time,
    }


def insert_trades(trades: List[TradeModel]) -> None:
    """SQLTransaction containing List[TradeModel] INSERT

    :param trades: List of trades to insert
    :return : None
    """
    if len(trades) == 0:
        logging.warning("No trades provided")
        return
    # SQLAlchemy Core
    trades_dict = [_trade_model_to_dict(trade) for trade in trades]
    engine = DBSession.get_engine()
    with engine.connect() as conn:
        try:
            insert_obj = Trade.__table__.insert()
            conn.execute(insert_obj, trades_dict)
            conn.commit()
        except Exception as e:
            logging.warning(f"did not add trades")
            raise e
