from datetime import datetime
import time
import glob
import logging
import os
import sys

from configurations.config import get_cache_dir_sys


def cleanup_logs(log_dir, days=1):
    now = time.time()
    print(f"current time: {now}")

    for file_path in glob.glob(os.path.join(log_dir, "*.log")):
        try:
            print(f"Checking log file: {file_path}")
            if os.stat(file_path).st_mtime < now - days * 86400:
                os.remove(file_path)
                print(f"Deleted log file: {file_path}")
        except FileNotFoundError:
            print(f"File not found (skipping): {file_path}")
        except PermissionError:
            print(f"Permission denied (skipping): {file_path}")
        except Exception as e:
            print(f"Error deleting file {file_path}: {e}")


def init_log(log_file_template: str):
    config_dir = get_cache_dir_sys()

    cleanup_logs(config_dir)

    ts = datetime.now().strftime("%Y%m%d_%H%M")

    log_file = log_file_template.format(ts=ts)
    log_file = os.path.join(config_dir, log_file)

    log_dir = os.path.dirname(log_file)
    print(f"Log directory: {log_dir}")

    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
    print(f"Log directory: {log_dir}")

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Supprime les anciens handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S"
    )

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.ERROR)
    root_logger.addHandler(console_handler)
