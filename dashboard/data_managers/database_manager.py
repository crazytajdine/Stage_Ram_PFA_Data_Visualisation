from contextlib import contextmanager
import os
import threading
import time
import logging
from sqlalchemy import create_engine as sa_create_engine
from sqlalchemy.exc import SQLAlchemyError
from configurations.config import get_base_config
from dotenv import load_dotenv

from sqlalchemy.orm import sessionmaker


load_dotenv()

config = get_base_config()

engine = None
engine_reconnect_thread = None
_reconnect_lock = threading.Lock()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=None)


def init_engine():
    global engine, SessionLocal
    password = os.getenv("DB_PASSWORD", "")
    url = (
        f"{config['driver']}://{config['user']}:{password}@"
        f"{config['host']}:{config['port']}/{config['name']}"
    )
    try:
        eng = sa_create_engine(url, pool_pre_ping=True, pool_recycle=1800, future=True)
        # test connection
        with eng.connect() as conn:
            conn.execute("SELECT 1")
        engine = eng
        SessionLocal.configure(bind=engine)
        logging.info(f"Database engine created with URL: {url}")
    except SQLAlchemyError as e:
        engine = None
        url = (
            f"{config['driver']}://{config['user']}:####@"
            f"{config['host']}:{config['port']}/{config['name']}"
        )
        logging.error(f"Failed to create database engine with URL: {url} - Error: {e}")


def get_session():
    global SessionLocal
    if engine is None:
        raise Exception("Database engine not available")
    # bind the sessionmaker to the current engine

    return SessionLocal()


@contextmanager
def session_scope(commit: bool = True):
    session = get_session()
    try:
        yield session
        if commit:
            session.commit()

    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def background_engine_reconnector(interval_seconds=10):
    global engine
    while True:
        if engine is None:
            logging.info("Background: DB engine is None, trying to reconnect...")
            init_engine()
        time.sleep(interval_seconds)


def start_engine_reconnect_thread():
    global engine_reconnect_thread
    with _reconnect_lock:
        if engine_reconnect_thread is None:
            logging.info("Starting background DB engine reconnect thread (startup)")
            engine_reconnect_thread = threading.Thread(
                target=background_engine_reconnector, daemon=True
            )
            engine_reconnect_thread.start()


def get_engine():
    global engine, engine_reconnect_thread
    if engine is None and engine_reconnect_thread is None:
        start_engine_reconnect_thread()
    return engine


if engine is None and engine_reconnect_thread is None:
    start_engine_reconnect_thread()
