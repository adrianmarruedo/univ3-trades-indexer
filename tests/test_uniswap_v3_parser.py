import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from src.parsers.uniswap_v3_parser import UniswapV3Parser
from src.models.log_model import LogModel
from src.models.uniswap_v3 import SwapEventModel
from src.models.trade_model import TradeModel
from src.constants.evm import UNISWAP_V3_SWAP_TOPIC, DEFAULT_DECIMALS


class TestUniswapV3Parser:
    """Test cases for UniswapV3Parser"""
    
    @pytest.fixture
    def parser(self):
        """Create a parser instance for testing"""
        return UniswapV3Parser(
            pool_address="0xcbcdf9626bc03e24f779434178a73a0b4bad62ed",
            token_address_0="0xA0b86a33E6441d9C64b7Ef8d8b7b1E8F8B8E8B8E",  # USDC
            token_address_1="0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",  # WETH
            decimals_0=6,   # USDC decimals
            decimals_1=18   # ETH decimals
        )
    
    @pytest.fixture
    def valid_swap_log(self):
        """Create a valid swap log for testing using real Uniswap V3 swap data"""
        return LogModel(
            chain_id=1,
            block_num=18500000,
            block_hash="0xabcd1234567890abcdef1234567890abcdef1234567890abcdef1234567890ab",
            address="0xcbcdf9626bc03e24f779434178a73a0b4bad62ed",  # Real WBTC pool address
            topic=UNISWAP_V3_SWAP_TOPIC,
            topics=[
                UNISWAP_V3_SWAP_TOPIC,
                "0x000000000000000000000000E592427A0AEce92De3Edee1F18E0157C05861564",  # Real sender
                "0x000000000000000000000000dd57A4bF3F3cBE2d2E52F57510C90DFe28aA882c"   # Real recipient
            ],
            # Real swap data from Ethereum mainnet
            data="0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffff20e34a" +
                 "0000000000000000000000000000000000000000000000001bc16d674ec80000" +
                 "000000000000000000000000000000000005a286057cdb9b565fd0f99488a852" +
                 "00000000000000000000000000000000000000000000000008af6b6b02a3e296" +
                 "000000000000000000000000000000000000000000000000000000000003e98f",
            transaction_hash="0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
            log_index=42,
            deleted=False,
            block_time=datetime(2023, 10, 15, 12, 30, 45)
        )

    def test_parse_swap_log_valid_buy(self, parser, valid_swap_log):
        """Test parsing a valid BUY swap log"""
        result = parser.parse_swap_log(valid_swap_log)
        
        assert result is not None
        assert isinstance(result, SwapEventModel)
        assert result.chain_id == 1
        assert result.block_num == 18500000
        assert result.tx_hash == "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
        assert result.log_index == 42
        assert result.pool_address == "0xcbcdf9626bc03e24f779434178a73a0b4bad62ed"
        assert result.sender == "0xe592427a0aece92de3edee1f18e0157c05861564"
        assert result.recipient == "0xdd57a4bf3f3cbe2d2e52f57510c90dfe28aa882c"
        assert result.decimals_0 == 6
        assert result.decimals_1 == 18
        assert result.trade_type in ["BUY", "SELL"]
        assert result.amount_0 == "-14621878"  # Negative WBTC amount (selling WBTC)
        assert result.amount_1 == "2000000000000000000"  # Positive ETH amount (buying ETH)
        assert result.trade_type == "BUY"  # amount0 < 0 means buying token1 (ETH)
        assert result.block_time == datetime(2023, 10, 15, 12, 30, 45)

    def test_parse_swap_log_invalid_topic(self, parser, valid_swap_log):
        """Test parsing log with invalid topic"""
        valid_swap_log.topics[0] = "0xinvalidtopic1234567890abcdef1234567890abcdef1234567890abcdef12345"
        
        result = parser.parse_swap_log(valid_swap_log)
        assert result is None

    def test_parse_swap_log_insufficient_topics(self, parser, valid_swap_log):
        """Test parsing log with insufficient topics"""
        valid_swap_log.topics = [UNISWAP_V3_SWAP_TOPIC]  # Missing sender and recipient
        
        result = parser.parse_swap_log(valid_swap_log)
        assert result is None

    def test_parse_swap_log_invalid_data(self, parser, valid_swap_log):
        """Test parsing log with invalid data"""
        valid_swap_log.data = "0xinvaliddata"
        
        result = parser.parse_swap_log(valid_swap_log)
        assert result is None

    @patch('src.parsers.uniswap_v3_parser.decode')
    def test_parse_swap_log_decode_exception(self, mock_decode, parser, valid_swap_log):
        """Test parsing log when decode raises exception"""
        mock_decode.side_effect = Exception("Decode failed")
        
        result = parser.parse_swap_log(valid_swap_log)
        assert result is None

    def test_decode_address(self, parser):
        """Test address decoding from topics"""
        topic = "0x000000000000000000000000e592427a0aece92de3edee1f18e0157c05861564"
        expected = "0xe592427a0aece92de3edee1f18e0157c05861564"
        
        result = parser._decode_address(topic)
        assert result == expected

    def test_decode_address_without_prefix(self, parser):
        """Test address decoding without 0x prefix"""
        topic = "000000000000000000000000e592427a0aece92de3edee1f18e0157c05861564"
        expected = "0xe592427a0aece92de3edee1f18e0157c05861564"
        
        result = parser._decode_address(topic)
        assert result == expected

    def test_conform_trades_valid(self, parser):
        """Test converting SwapEventModel to TradeModel"""
        swap_event = SwapEventModel(
            chain_id=1,
            block_num=18500000,
            tx_hash="0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
            log_index=42,
            pool_address="0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640",
            sender="0xe592427a0aece92de3edee1f18e0157c05861564",
            recipient="0x742d35cc6634c0532925a3b8d2b9e4e8c4e8c4e8",
            amount_0="-1000000",
            amount_1="1000000000000000000",
            token_address_0="0xA0b86a33E6441d9C64b7Ef8d8b7b1E8F8B8E8B8E",
            token_address_1="0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
            decimals_0=6,
            decimals_1=18,
            trade_type="BUY",
            sqrt_price_x96="1234567890123456789012345678901234567890",
            tick=-276324,
            liquidity="12345678901234567890",
            block_time=datetime(2023, 10, 15, 12, 30, 45)
        )
        
        result = parser.conform_trades(swap_event)
        
        assert isinstance(result, TradeModel)
        assert result.chain_id == swap_event.chain_id
        assert result.block_num == swap_event.block_num
        assert result.tx_hash == swap_event.tx_hash
        assert result.log_index == swap_event.log_index
        assert result.type == swap_event.trade_type
        assert result.pool_address == swap_event.pool_address
        assert result.sender == swap_event.sender
        assert result.recipient == swap_event.recipient
        assert result.amount_0 == swap_event.amount_0
        assert result.amount_1 == swap_event.amount_1
        assert result.decimals_0 == swap_event.decimals_0
        assert result.decimals_1 == swap_event.decimals_1
        assert result.token_address_0 == swap_event.token_address_0
        assert result.token_address_1 == swap_event.token_address_1
        assert result.block_time == swap_event.block_time

    def test_conform_trades_exception(self, parser):
        """Test conform_trades with invalid data raises exception"""
        # Create invalid swap event (missing required fields)
        invalid_swap = Mock()
        invalid_swap.chain_id = None  # This should cause an error
        
        with pytest.raises(Exception):
            parser.conform_trades(invalid_swap)
