import pickle
import threading
import time
from typing import Any, Literal, Optional
import redis
import logging
import functools
from utils_dashboard.utils_filter import get_filter_list

NAME_TABLE = "calculations"

redis_server: Optional[redis.Redis] = None
redis_reconnect_thread: Optional[threading.Thread] = None
_reconnect_lock = threading.Lock()


def get_redis_server() -> Optional[redis.Redis]:
    global redis_server, redis_reconnect_thread
    if redis_server is None and redis_reconnect_thread is None:
        start_redis_reconnect_thread()
    return redis_server


def join_key(*args: str) -> str:
    key = ":".join((NAME_TABLE, *args))
    logging.debug(f"join_key called with args={args}, returning key='{key}'")
    return key


def does_key_exist(key: str) -> Optional[bool]:

    r = get_redis_server()
    if r is None:
        return None
    exists = bool(r.exists(key))
    logging.debug(f"does_key_exist: key='{key}', exists={exists}")
    return exists


def does_table_exist() -> Optional[bool]:

    r = get_redis_server()

    if r is None:
        return None
    exists = bool(r.exists(NAME_TABLE))
    logging.debug(f"does_table_exist: table='{NAME_TABLE}', exists={exists}")
    return exists


def init_server() -> Optional[redis.Redis]:
    global redis_server
    from dashboard.configurations.config import get_base_config

    config = get_base_config()

    config_host = config.get("redis", {}).get("host", "localhost")
    config_port = config.get("redis", {}).get("port", 6379)
    config_db = config.get("redis", {}).get("db", 0)

    logging.info(
        f"Initializing Redis server with host={config_host}, port={config_port}, db={config_db}"
    )
    r = redis.Redis(host=config_host, port=config_port, db=config_db)

    try:
        r.ping()
        logging.info("Redis connected")
        redis_server = r

    except redis.exceptions.RedisError as e:
        logging.error("Redis connection failed during init: %s", e)
        redis_server = None


def delete_old_keys() -> Optional[bool]:

    r = get_redis_server()

    if r is None:
        return None

    pattern = join_key("*")
    keys = r.keys(pattern)
    logging.info(f"Deleting keys with pattern '{pattern}': found {len(keys)} keys.")

    deleted_all = True
    for key in keys:
        try:
            result = r.delete(key)
            deleted_all = deleted_all and bool(result)
            logging.debug(f"Deleted key: {key}, success: {bool(result)}")
        except Exception as e:
            logging.error(f"Failed to delete key {key}: {e}")
            deleted_all = False
    logging.info(f"All keys deleted successfully: {deleted_all}")
    return deleted_all


def set_calculation_to_cache(
    key: str, value: Any, expire_seconds: Optional[int] = None
) -> Optional[bool]:
    r = get_redis_server()
    if r is None:
        return None
    try:
        json_value = pickle.dumps(value)
        result = r.set(key, json_value, ex=expire_seconds)
        logging.info(f"Set cache key='{key}' with value={value}, success={result}")
        return bool(result)
    except Exception as e:
        logging.error(f"Failed to set cache for key '{key}': {e}")
        return False


def get_calculation_from_cache(key) -> Any:
    r = get_redis_server()
    if r is None:
        return None
    try:
        cached_value = r.get(key)
        if cached_value is not None:
            result = pickle.loads(cached_value)
            logging.info(f"Cache hit for key='{key}'.")
            return result
        else:
            logging.info(f"Cache miss for key='{key}'.")
            return None
    except Exception as e:
        logging.error(f"Failed to get cache for key '{key}': {e}")
        return None


def cache_result(redis_key_prefix: str, expire_seconds: int = 3600):

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            key = join_key(*get_filter_list(), redis_key_prefix)
            cached = get_calculation_from_cache(key)
            if cached is not None:
                logging.debug(f"Cache hit for key {key}")
                return cached
            logging.debug(f"Cache miss for key {key}, running function.")
            result = func(*args, **kwargs)
            try:
                set_calculation_to_cache(key, result, expire_seconds)
            except Exception as e:
                logging.warning(f"Failed to cache result for key {key}: {e}")
            return result

        return wrapper

    return decorator


def background_redis_reconnector(interval_seconds=10):
    global redis_server
    while True:
        if redis_server is None:
            logging.info("Background: Redis is None, trying to reconnect...")
            init_server()
        time.sleep(interval_seconds)


def start_redis_reconnect_thread():
    global redis_reconnect_thread
    with _reconnect_lock:
        if redis_reconnect_thread is None:
            logging.info(f"Starting background Redis reconnect thread (startup)")
            redis_reconnect_thread = threading.Thread(
                target=background_redis_reconnector, daemon=True
            )
            redis_reconnect_thread.start()


if redis_reconnect_thread is None and redis_server is None:

    start_redis_reconnect_thread()
