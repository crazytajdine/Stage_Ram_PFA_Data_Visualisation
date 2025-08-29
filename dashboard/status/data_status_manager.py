import logging

from schemas.data_status import StatusData
from dash import Input, State, dcc

start: StatusData = "unselected"

ID_DATA_STATUS_CHANGE_TRIGGER = "store-status-data-trigger"
store_trigger_status = dcc.Store(ID_DATA_STATUS_CHANGE_TRIGGER, data=start)


def add_watcher_for_data_status():
    return Input(ID_DATA_STATUS_CHANGE_TRIGGER, "data")


def add_state_for_data_status():
    return State(ID_DATA_STATUS_CHANGE_TRIGGER, "data")
