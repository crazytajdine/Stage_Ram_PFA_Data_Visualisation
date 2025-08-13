from contextlib import contextmanager
import os
import logging
from sqlalchemy import create_engine as sa_create_engine
from sqlalchemy.exc import SQLAlchemyError
from configurations.config import get_base_config
from dotenv import load_dotenv

from sqlalchemy.orm import sessionmaker, Session

from data_managers.unitializers.database_seed import initialize_database_first_time
from schemas.database_models import Base

load_dotenv()

config = get_base_config()

engine = None

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=None)


@contextmanager
def session_scope(commit: bool = True):

    session = get_session()
    try:
        yield session
        if commit:
            session.commit()
    except Exception:
        if commit:
            session.rollback()
        raise
    finally:
        session.close()


def init_engine():
    global engine, SessionLocal
    if engine is not None:
        return

    user = os.getenv("DB_USER", "")
    password = os.getenv("DB_PASSWORD", "")
    dbname = os.getenv("DB_NAME", "")
    config_database = config.get("database", {})
    url = (
        f"{config_database['driver']}://{user}:{password}@"
        f"{config_database['host']}:{config_database['port']}/{dbname}"
    )
    try:
        eng = sa_create_engine(url, pool_pre_ping=True, pool_recycle=1800, future=True)
        Base.metadata.create_all(eng)
        engine = eng
        SessionLocal.configure(bind=engine)
        logging.info(f"Database engine created with URL: {url}")
    except SQLAlchemyError as e:
        engine = None
        SessionLocal.configure(bind=None)
        url = (
            f"{config_database['driver']}://####:####@"
            f"{config_database['host']}:{config_database['port']}/####"
        )

        logging.error(f"Failed to create database engine with URL: {url} - Error: {e}")
        raise e


def get_session() -> Session:
    global SessionLocal
    if engine is None:
        raise Exception("Database engine not available")
    # bind the sessionmaker to the current engine

    return SessionLocal()


def get_engine():
    global engine
    if engine is None:
        init_engine()
    return engine


init_engine()
with session_scope() as session:

    initialize_database_first_time(session)
