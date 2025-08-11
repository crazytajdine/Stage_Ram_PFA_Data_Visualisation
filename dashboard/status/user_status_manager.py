import logging

from schemas.data_status import statusUser


status: statusUser = "unverified"


def compare_status(new_status: statusUser) -> bool:
    return status == new_status


def set_status(new_status: statusUser):
    global status
    if status != new_status:
        status = new_status
        logging.info("Status data changed to %s", status)
