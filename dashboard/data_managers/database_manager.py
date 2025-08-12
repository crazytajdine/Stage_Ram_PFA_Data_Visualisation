import os
import threading
import time
import logging
from sqlalchemy import create_engine as sa_create_engine
from sqlalchemy.exc import SQLAlchemyError
from configurations.config import get_base_config
from dotenv import load_dotenv

load_dotenv()

config = get_base_config()

engine = None
engine_reconnect_thread = None
_reconnect_lock = threading.Lock()


def init_engine():
    global engine
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
        logging.info(f"Database engine created with URL: {url}")
    except SQLAlchemyError as e:
        engine = None
        url = (
            f"{config['driver']}://{config['user']}:####@"
            f"{config['host']}:{config['port']}/{config['name']}"
        )
        logging.error(f"Failed to create database engine with URL: {url} - Error: {e}")


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
