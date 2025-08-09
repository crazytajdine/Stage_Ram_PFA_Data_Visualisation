import json
from typing import Any, Optional
import redis
import logging
import functools

redis_server: redis.Redis = None
NAME_TABLE = "calculations"


def get_redis_server() -> redis.Redis:
    global redis_server

    if redis_server is None:
        logging.debug("Redis server not initialized, initializing now.")

        init_server()
    return redis_server


def join_key(*args: str) -> str:
    key = ":".join((NAME_TABLE, *args))
    logging.debug(f"join_key called with args={args}, returning key='{key}'")
    return key


def does_key_exist(key: str) -> bool:

    r = get_redis_server()

    exists = bool(r.exists(key))
    logging.debug(f"does_key_exist: key='{key}', exists={exists}")
    return exists


def does_table_exist() -> bool:

    r = get_redis_server()

    if r is None:
        logging.debug("Redis server not initialized, initializing now.")
        init_server()

    exists = bool(r.exists(NAME_TABLE))
    logging.debug(f"does_table_exist: table='{NAME_TABLE}', exists={exists}")
    return exists


def init_server():

    r = get_redis_server()

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
        # Test connection
        r.ping()
        logging.info("Redis server connection successful.")
    except redis.exceptions.ConnectionError as e:
        logging.error(f"Redis connection failed: {e}")
        r = None

    return r


def delete_old_keys() -> bool:

    r = get_redis_server()

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
) -> bool:
    r = get_redis_server()

    try:
        json_value = json.dumps(value)
        result = r.set(key, json_value, ex=expire_seconds)
        logging.info(f"Set cache key='{key}' with value={value}, success={result}")
        return bool(result)
    except Exception as e:
        logging.error(f"Failed to set cache for key '{key}': {e}")
        return False


def get_calculation_from_cache(key) -> Any:
    r = get_redis_server()

    try:
        cached_value = r.get(key)
        if cached_value is not None:
            result = json.loads(cached_value)
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
            key = join_key(redis_key_prefix)
            cached = get_calculation_from_cache(key)
            if cached:
                logging.debug(f"Cache hit for key {key}")
                return json.loads(cached)
            logging.debug(f"Cache miss for key {key}, running function.")
            result = func(*args, **kwargs)
            try:
                set_calculation_to_cache(key, result, expire_seconds)
            except Exception as e:
                logging.warning(f"Failed to cache result for key {key}: {e}")
            return result

        return wrapper

    return decorator
