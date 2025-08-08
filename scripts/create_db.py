import logging

from config import settings
from src.db import Base
from src.db.db_utils import create_tables, create_database

logger = logging.getLogger()
logger.setLevel(level=logging.INFO)


if __name__ == "__main__":
    create_database()
    create_tables(metadata=Base.metadata)
