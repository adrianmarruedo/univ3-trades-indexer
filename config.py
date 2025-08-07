from dotenv import load_dotenv
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    # Database settings
    POSTGRES_HOST: str
    POSTGRES_USER: str
    POSTGRES_PASS: str
    POSTGRES_PORT: int
    POSTGRES_DATABASE: str

    # Web3 provider settings
    PROVIDER_URL: str
    PROVIDER_WEBSOCKET: str
    PROVIDER_KEY: str
    
    # Kafka settings
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"


load_dotenv()
settings = Config()