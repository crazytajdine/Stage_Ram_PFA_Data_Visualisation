import logging

from schemas.data_status import StatusData


status: StatusData = "unselected"


def compare_status(new_status: StatusData) -> bool:
    return status == new_status


def set_status(new_status: StatusData):
    global status
    if status != new_status:
        status = new_status
        logging.info("Status data changed to %s", status)
