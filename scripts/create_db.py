import logging

from src.db import Base
from src.db.db_utils import create_tables

logger = logging.getLogger()
logger.setLevel(level=logging.INFO)


if __name__ == "__main__":
    create_tables(metadata=Base.metadata)
