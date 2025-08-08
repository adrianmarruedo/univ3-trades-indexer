import logging

from sqlalchemy import create_engine
from sqlalchemy.schema import MetaData
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from config import settings


class DBSession:
    """DBSession class preparing to be scalable to multiple connections"""
    @classmethod
    def get_engine(cls) -> Engine:
        """Create SQL Alchemy Engine based on Postgres"""
        engine_url = f"postgresql+psycopg2://{settings.POSTGRES_USER}:{settings.POSTGRES_PASS}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DATABASE}"
        engine = create_engine(engine_url, future=True, echo=False)

        return engine

    @classmethod
    def get_db(cls) -> sessionmaker:
        """Return SQL Alchemy sessionmaker"""
        engine = cls.get_engine()
        session = sessionmaker(engine)

        return session


def create_tables(metadata: MetaData) -> None:
    try:
        metadata.create_all(DBSession.get_engine())
    except Exception as e:
        logging.error(e)
        logging.warning("Unsuccessful Tables Creation")
        

def create_database():
    try:
        engine = create_engine(
            f"postgresql+psycopg2://{settings.POSTGRES_USER}:{settings.POSTGRES_PASS}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/postgres", 
            future=True,
            echo=False
        )
        
        result = engine.execute(
            text(f"SELECT 1 FROM pg_database WHERE datname = '{settings.POSTGRES_DATABASE}'")
        )
        if result.fetchone():
            logging.info(f"Database '{settings.POSTGRES_DATABASE}' exists")
        else:
            engine.execute(text(f"CREATE DATABASE {settings.POSTGRES_DATABASE}"))
            logging.info("Database created successfully")
        
    except Exception as e:
        logging.error(e)
        logging.warning("Unsuccessful Database Creation")
