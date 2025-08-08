import logging
import time
import asyncio
import json
from typing import Dict, List, AsyncGenerator

from web3 import Web3
import websockets

from src.models import LogModel

logger = logging.getLogger()


class AlchemyProvider:
    """Alchemy provider Class"""

    def __init__(self, chain_id: int, host: str, websocket: str, api_key: str) -> None:
        self.chain_id = chain_id
        self._url = host
        self._websocket_url = websocket + api_key if not websocket.endswith(api_key) else websocket
        self._web3 = Web3(Web3.HTTPProvider(host + api_key))
        
        if not self._web3.is_connected():
            raise Exception("Failed to connect to Web3 provider")
            
        # WebSocket connection will be established when needed
        self._websocket = None
        self._subscription_id = None

    async def _connect_websocket(self):
        """Establish WebSocket connection to Alchemy"""
        try:
            self._websocket = await websockets.connect(self._websocket_url)
            logger.info("WebSocket connected")
            return True
        except Exception as e:
            logger.error(f"Failed to connect WebSocket: {e}")
            return False
    
    async def _subscribe_to_logs(self, contract_address: str, topics: List[str]):
        """Subscribe to real-time logs via WebSocket"""
        if not self._websocket:
            if not await self._connect_websocket():
                raise Exception("Failed to establish WebSocket connection")
        
        subscription_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "eth_subscribe",
            "params": [
                "logs",
                {
                    "address": contract_address,
                    "topics": topics
                }
            ]
        }
        
        await self._websocket.send(json.dumps(subscription_request))
        response = await self._websocket.recv()
        response_data = json.loads(response)
        
        if "result" in response_data:
            self._subscription_id = response_data["result"]
            logger.info(f"Subscribed to logs with subscription ID: {self._subscription_id}")
            return True
        else:
            logger.error(f"Failed to subscribe: {response_data}")
            return False

    def parse_log(self, log) -> LogModel:
        """Returns the LogModel of the given log AttrDict"""
        try:
            log_model = LogModel(
                chain_id=self.chain_id,
                block_num=log["blockNumber"],
                block_hash=self._web3.to_hex(log["blockHash"]),
                transaction_hash=self._web3.to_hex(log["transactionHash"]),
                address=str(log["address"]),
                topic=self._web3.to_hex(log["topics"][0]) if len(log["topics"]) else None,
                topics=[self._web3.to_hex(topic) for topic in log["topics"]],
                data=self._web3.to_hex(log["data"]),
                log_index=log["logIndex"],
                deleted=log["removed"],
                block_time=None
            )
            return log_model
        
        except Exception as e:
            logger.error(f"Error Log: {log}")
            raise e

    def parse_log_dict(self, log) -> LogModel:
        """Returns the LogModel of the given log Dict from response json"""
        try:
            log_model = LogModel(
                chain_id=self.chain_id,
                block_num=self._web3.to_int(hexstr=log["blockNumber"]),
                block_hash=log["blockHash"],
                transaction_hash=log["transactionHash"],
                address=log["address"],
                topic=log["topics"][0] if len(log["topics"]) else None,
                topics=log["topics"],
                data=log["data"],
                log_index=self._web3.to_int(hexstr=log["logIndex"]),
                deleted=bool(log["removed"]),
                block_time=None
            )
            return log_model
        
        except Exception as e:
            logger.error(f"Error Log: {log}")
            raise e

    def get_latest_block_num(self) -> int:
        """Returns last block number"""
        return self._web3.eth.block_number

    def get_logs(self, start_block: int, end_block: int) -> List[LogModel]:
        """Returns List of logs between the range conformed to LogModel"""
        assert end_block >= start_block

        logs = []
        st = time.time()

        event_filter = {"fromBlock": start_block, "toBlock": end_block}
        logs_provider = self._web3.eth.get_logs(event_filter)
        for log in logs_provider:
            logs.append(self.parse_log(log))
        et = time.time()
        logger.debug(f"get_logs time: {et-st} seconds")

        return logs

    def get_logs_filtered(self, filter_dict: Dict) -> List[LogModel]:
        """Returns List of logs conformed to LogModel applying the EthFilter in filter_dict"""
        logs = []
        st = time.time()

        logs_provider = self._web3.eth.get_logs(filter_dict)
        for log in logs_provider:
            logs.append(self.parse_log(log))
        et = time.time()
        logger.debug(f"get_logs_filtered time: {et-st} seconds") 

        return logs

    def checksum_address(self, contract_address: str) -> str:
        return self._web3.to_checksum_address(contract_address)
    
    def create_event_filter(self, contract_address: str, topics: List[str]):
        """Create an event filter for the specified contract and topics"""
        return self._web3.eth.filter({
            'address': contract_address,
            'topics': topics
        })
    
    def latest_block_number(self) -> int:
        return self._web3.eth.block_number
    
    async def listen_for_events_realtime(self, contract_address: str, topics: List[str]) -> AsyncGenerator[LogModel, None]:
        """Listen for real-time events via WebSocket"""
        try:
            if not await self._subscribe_to_logs(contract_address, topics):
                raise Exception("Failed to subscribe to logs")
            
            logger.info("Starting real-time event listening via WebSocket...")
            
            while True:
                try:
                    # Use timeout to allow periodic checks for shutdown
                    message = await asyncio.wait_for(self._websocket.recv(), timeout=1.0)
                    
                    data = json.loads(message)
                    
                    if (data["method"] == "eth_subscription" and 
                        data["params"]["subscription"] == self._subscription_id):
                        
                        log_data = data["params"]["result"]
                        log_model = self.parse_log_dict(log_data)
                        
                        logger.debug(f"Received real-time log: block {log_model.block_num}, tx {log_model.transaction_hash}")
                        yield log_model
                        
                except asyncio.TimeoutError:
                    # Timeout allows for graceful shutdown checks
                    continue
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse WebSocket message: {e}")
                    continue
                except Exception as e:
                    logger.error(f"Error processing WebSocket message: {e}")
                    continue
                    
        except websockets.exceptions.ConnectionClosed:
            logger.warning("WebSocket connection closed")
            raise
        except Exception as e:
            logger.error(f"Error in event listening: {e}")
            raise
        finally:
            await self._cleanup_websocket()
    
    async def _cleanup_websocket(self):
        """Clean up WebSocket connection and subscription"""
        try:
            if self._websocket and self._subscription_id:
                # Unsubscribe before closing
                unsubscribe_request = {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "eth_unsubscribe",
                    "params": [self._subscription_id]
                }
                
                await asyncio.wait_for(
                    self._websocket.send(json.dumps(unsubscribe_request)), 
                    timeout=2.0
                )
                logger.info(f"Unsubscribed from subscription {self._subscription_id}")
            
            if self._websocket:
                await self._websocket.close()
                logger.info("WebSocket connection closed")
                
        except Exception as e:
            logger.error(f"Error during WebSocket cleanup: {e}")
        finally:
            self._websocket = None
            self._subscription_id = None