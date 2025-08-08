import json
import logging
from typing import Dict, Any, Callable

from kafka import KafkaConsumer
from kafka.errors import KafkaError

logger = logging.getLogger(__name__)


class TradeEventConsumer:
    
    def __init__(self, bootstrap_servers: str, group_id: str = "trade-processor"):
        self.bootstrap_servers = bootstrap_servers
        self.group_id = group_id
        self.consumer = None
        self._connect()
    
    def _connect(self):
        try:
            self.consumer = KafkaConsumer(
                bootstrap_servers=self.bootstrap_servers,
                group_id=self.group_id,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                key_deserializer=lambda k: k.decode('utf-8') if k else None,
                auto_offset_reset='earliest',  # Start from beginning if no offset
                enable_auto_commit=True,
                auto_commit_interval_ms=1000,
                session_timeout_ms=30000,
                heartbeat_interval_ms=10000
            )
            logger.info(f"Kafka consumer connected to {self.bootstrap_servers} with group_id: {self.group_id}")
        except Exception as e:
            logger.error(f"Failed to connect to Kafka: {e}")
            raise
    
    def subscribe(self, topics: list):
        try:
            if not self.consumer:
                self._connect()
            
            self.consumer.subscribe(topics)
            logger.info(f"Subscribed to topics: {topics}")
        except Exception as e:
            logger.error(f"Failed to subscribe to topics {topics}: {e}")
            raise
    
    def consume_messages(self, message_handler: Callable[[Dict[str, Any]], None], running_flag=None):
        try:
            logger.info("Starting message consumption...")
            
            while True:
                # Check if we should stop (if running_flag is provided)
                if running_flag is not None and not running_flag():
                    logger.info("Stopping message consumption due to shutdown signal")
                    break
                
                # Poll for messages with timeout to allow checking running_flag
                message_batch = self.consumer.poll(timeout_ms=1000)
                
                if not message_batch:
                    continue  # No messages, continue polling
                
                for topic_partition, messages in message_batch.items():
                    for message in messages:
                        # Check shutdown signal before processing each message
                        if running_flag is not None and not running_flag():
                            logger.info("Stopping message processing due to shutdown signal")
                            return
                        
                        try:
                            trade_data = message.value
                            message_key = message.key
                            
                            logger.debug(f"Received message from topic {message.topic}, partition {message.partition}, offset {message.offset}")
                            
                            message_handler(trade_data)
                            
                        except Exception as e:
                            logger.error(f"Error processing message: {e}")
                            continue
                    
        except KafkaError as e:
            logger.error(f"Kafka error during consumption: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during consumption: {e}")
            raise
        finally:
            self.close()
    
    def close(self):
        if self.consumer:
            self.consumer.close()
            logger.info("Kafka consumer closed")
