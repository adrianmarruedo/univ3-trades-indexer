CHAIN_ID = 1

DEFAULT_DECIMALS = 18

USDC_ETH_POOL_ADDRESS = "0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640"
NULL_ADDRESS = "0x0000000000000000000000000000000000000000"
USDC = "0xA0b86a33E6441d9C64b7Ef8d8b7b1E8F8B8E8B8E"
WETH = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"

# Trade Names
TRADE = "Trade"
TRADE_UNISWAP_V3_SWAP = "UniswapV3Swap"

# Trades Topics
UNISWAP_V3_SWAP_TOPIC = "0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67"  # Swap event signature

TRADE_TOPICS = [
    {
        "name": TRADE_UNISWAP_V3_SWAP,
        "signature": UNISWAP_V3_SWAP_TOPIC,
        "count": 3
    },
    # ... Add more available topics
]


UNISWAP_V3_SWAP_ABI = {
    "anonymous": False,
    "inputs": [
        {
            "indexed": True,
            "internalType": "address",
            "name": "sender",
            "type": "address"
        },
        {
            "indexed": True,
            "internalType": "address",
            "name": "recipient",
            "type": "address"
        },
        {
            "indexed": False,
            "internalType": "int256",
            "name": "amount0",
            "type": "int256"
        },
        {
            "indexed": False,
            "internalType": "int256",
            "name": "amount1",
            "type": "int256"
        },
        {
            "indexed": False,
            "internalType": "uint160",
            "name": "sqrtPriceX96",
            "type": "uint160"
        },
        {
            "indexed": False,
            "internalType": "uint128",
            "name": "liquidity",
            "type": "uint128"
        },
        {
            "indexed": False,
            "internalType": "int24",
            "name": "tick",
            "type": "int24"
        },
    ],
    "name": "Swap",
    "type": "event"
}
