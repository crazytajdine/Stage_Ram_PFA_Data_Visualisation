import os
import dash
import logging

from dash import Input, Output, State

from schemas.data_status import StatusData
from data_managers.excel_manager import (
    ID_INTERVAL_WATCHER,
    ID_PATH_STORE,
    ID_STORE_DATE_WATCHER,
    add_state_for_data_status,
    get_latest_modification_time,
    get_path_to_excel,
    modify_modification_date,
    update_df_unfiltered,
)
from server_instance import get_app


app = get_app()


def add_callbacks():
    @app.callback(
        Output(ID_PATH_STORE, "data"),
        Output(ID_STORE_DATE_WATCHER, "data", allow_duplicate=True),
        State(ID_PATH_STORE, "data"),
        State(ID_STORE_DATE_WATCHER, "data"),
        Input(ID_INTERVAL_WATCHER, "n_intervals"),
        add_state_for_data_status(),
        prevent_initial_call=True,
    )
    def watch_file(current_path, date_latest_fetch, _, old_status):
        logging.debug("Watching file every second...")
        try:
            # Check if file path exists
            if (not current_path) or (not os.path.exists(current_path)):
                logging.warning("Excel file path no longer exists.")

                path_to_excel, latest_modification_time = (
                    get_path_to_excel(),
                    get_latest_modification_time(),
                )
                new_status: StatusData = "selected" if path_to_excel else "unselected"
                if old_status != new_status:

                    return path_to_excel, latest_modification_time
                else:
                    return dash.no_update
            # Check for modification time
            latest_modification_time = get_latest_modification_time()
            logging.debug(
                f"watching file: {latest_modification_time} new: {date_latest_fetch}"
            )
            if latest_modification_time != date_latest_fetch:
                logging.info("File changed, updating DataFrame...")
                update_df_unfiltered()

                modify_modification_date(latest_modification_time)
                return dash.no_update, latest_modification_time

        except FileNotFoundError:
            logging.warning("Excel file not found during watch.")

        except Exception as e:
            logging.error(f"Error watching file: {e}", exc_info=True)

        return dash.no_update
