import json
import logging
from typing import Dict, Any
from kafka import KafkaProducer
from kafka.errors import KafkaError

logger = logging.getLogger(__name__)


class TradeEventProducer:
    
    def __init__(self, bootstrap_servers: str):
        self.bootstrap_servers = bootstrap_servers
        self.producer = None
        self._connect()
    
    def _connect(self):
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                acks='all',
                retries=3,
                retry_backoff_ms=1000,
                max_in_flight_requests_per_connection=1,
                compression_type='gzip'
            )
            logger.info(f"Kafka producer connected to {self.bootstrap_servers}")
        except Exception as e:
            logger.error(f"Failed to connect to Kafka: {e}")
            raise
    
    def send_trade_event(self, topic: str, trade_data: Dict[str, Any], key: str = None):
        try:
            future = self.producer.send(topic, value=trade_data, key=key)
            
            record_metadata = future.get(timeout=10)
            
            logger.debug(f"Trade event sent to topic {topic}, partition {record_metadata.partition}, offset {record_metadata.offset}")
            return True
            
        except KafkaError as e:
            logger.error(f"Failed to send trade event to Kafka: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending trade event: {e}")
            return False
    
    def close(self):
        if self.producer:
            self.producer.close()
            logger.info("Kafka producer closed")
