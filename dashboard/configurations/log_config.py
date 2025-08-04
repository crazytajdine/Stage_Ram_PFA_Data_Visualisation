from datetime import datetime
import logging
import os
import sys


def init_log(LOG_FILE: str):
    log_dir = os.path.dirname(LOG_FILE)

    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M")

    LOG_FILE = LOG_FILE.format(ts=ts)

    logging.basicConfig(
        filename=LOG_FILE,
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        encoding="utf-8",
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)

    # Create formatter same as file formatter
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(formatter)

    # Add console handler to root logger
    logging.getLogger().addHandler(console_handler)
