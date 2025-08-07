import logging
from decimal import Decimal

from web3 import Web3

from src.utils import abi_utils
from src.models import LogModel, TradeModel
from src.constants import TRADE_TOPICS, TRADE_UNISWAP_V3_SWAP


logger = logging.getLogger()

web3 = Web3()


class TradeParser:
    """Trade Parser Class"""

    def decode_log(self, log: LogModel) -> TradeModel:
        """Returns a Model of the log data given the contract standard"""
        contract_type = self.trade_type_standard(log.topic, len(log.topics))

        if contract_type == TRADE_UNISWAP_V3_SWAP:
            return self._parse_uniswap_v3_swap_log(log)
        else:
            raise Exception("Wrong Trade Type")

    @staticmethod
    def _parse_uniswap_v3_swap_log(log: LogModel) -> TradeModel:
        topics = log.topics + abi_utils.split_to_words(log.data)
        args = { # TODO: Change
            "from": abi_utils.word_to_address(topics[1]),
            "to": abi_utils.word_to_address(topics[2]),
            "value": web3.to_int(hexstr=topics[3]),
        }

        result = TradeModel( # TODO: Change
            chain_id=log.chain_id,
            block_num=log.block_num,
            block_time=log.block_time,
            tx_hash=log.transaction_hash,
            tx_from=args["from"],
            tx_to=args["to"],
            value=Decimal(args["value"]),
            type="Transfer",
            token_address=log.address.lower(),
        )
        return result

    @staticmethod
    def trade_type_standard(topic: str, topics_count: int):
        """Returns if the topic is a trade standard"""
        if not topic:
            raise Exception("Anonymous Event")
        
        for available in TRADE_TOPICS:
            if available["signature"] == topic and available["count"] == topics_count:
                return available["name"]
        
        raise Exception("Topic is not part of the listed signatures")