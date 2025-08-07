from datetime import datetime
import logging
import os
import sys


def init_log(log_file_template: str):
    log_dir = os.path.dirname(log_file_template)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M")
    log_file = log_file_template.format(ts=ts)

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
    console_handler.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)
