from datetime import datetime, date
import os
from typing import Optional
import dash
import polars as pl
import logging

from dash import Input, Output, State, dcc

from configurations.config import get_user_config, save_config_sys
from server_instance import get_app

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [INFO] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logging.info("Loading excel file...")

# global

ID_PATH_STORE = "is-path-store"
ID_INTERVAL_WATCHER = "interval-file-selector"

ID_STORE_DATE_WATCHER = "store-date-latest-fetch"

COL_NAME_DEPARTURE_DATETIME = "DEP_DAY_SCHED"

COL_NAME_WINDOW_TIME = "WINDOW_DATETIME_DEP"
COL_NAME_WINDOW_TIME_MAX = "WINDOW_DATETIME_DEP_MAX"

COL_NAME_TOTAL_COUNT = "total_count"

ID_DATA_STORE_TRIGGER = "filter-store-trigger"

# init

app = get_app()

config = get_user_config()

path_to_excel = config.get("path_to_excel", "")
auto_refresh_disabled = config.get("auto_refresh", True)

count_excel_lazy = None


# func

def get_path_to_excel():
    return path_to_excel


def path_exits():
    if not path_to_excel:
        logging.debug("No path to Excel file configured.")
        return False

    is_exist = os.path.exists(path_to_excel)
    logging.debug(f"Path exists check: {is_exist} for path: {path_to_excel}")

    if not is_exist:
        return False

    is_file = os.path.isfile(path_to_excel)
    logging.debug(f"Is file check: {is_file} for path: {path_to_excel}")


    if not is_file:
        return False

    return True


def filter_tec(df_lazy: pl.LazyFrame) -> pl.LazyFrame:
    logging.info("Filtering technical delay codes from dataframe")
    try:
        filtered_df = df_lazy.filter(
            pl.col("CODE_DR").is_in([41, 42, 43, 44, 45, 46, 47, 51, 52, 55, 56, 57])
        )
        logging.debug("Filter applied on CODE_DR for technical delays")
        return filtered_df
    except Exception as e:
        logging.error(f"Error filtering technical delay codes: {e}", exc_info=True)
        return df_lazy


def filter_retard(df_lazy: pl.LazyFrame) -> pl.LazyFrame:
    logging.info("Filtering rows where 'Retard en min' is not zero")
    try:
        filtered_df = df_lazy.filter(pl.col("Retard en min") != 0)
        logging.debug("Filter applied on 'Retard en min' != 0")
        return filtered_df
    except Exception as e:
        logging.error(f"Error filtering retard data: {e}", exc_info=True)
        return df_lazy


def create_dep_datetime(df_lazy: pl.LazyFrame) -> pl.LazyFrame:
    logging.info("Creating combined departure datetime column")
    try:
        df_with_datetime = df_lazy.with_columns(
            pl.col("DEP_DAY_SCHED")
            .dt.combine(pl.col("DEP_TIME_SCHED").str.strptime(pl.Time, "%H:%M"))
            .alias(COL_NAME_DEPARTURE_DATETIME)
        )
        logging.debug(f"Added column '{COL_NAME_DEPARTURE_DATETIME}' combining date and time")
        return df_with_datetime
    except Exception as e:
        logging.error(f"Error creating departure datetime: {e}", exc_info=True)
        return df_lazy


def modify_modification_date(new_modification_date: float):
    global config

    config = save_config_sys({"modification_date": new_modification_date})

    logging.info(f"Set modification date to: {new_modification_date}")


def update_path_to_excel(path) -> tuple[bool, str]:
    global config, path_to_excel

    if not path:
        logging.warning("Provided path is empty.")

        return False, "Path cannot be empty."

    is_exist = os.path.exists(path)
    if not is_exist:
        logging.warning(f"File does not exist at path: {path}")

        return is_exist, "The excel file doesn't exist."

    is_file = os.path.isfile(path)

    if not is_file:
        logging.warning(f"Provided path is not a file: {path}")
        return (
            False,
            "The Path you provided is not for a file. Make sure it ends with '.excel' or another valid Excel format.",
        )

    try:
        load_excel_lazy(path)
    except Exception as e :
        logging.error(f"Error loading Excel file: {e}", exc_info=True)
        return False, "Could not load the file, make sure it is a valid excel file."

    path_to_excel = path

    config = save_config_sys({"path_to_excel": path})

    logging.info(f"Loaded the file successfully from: {path}")

    return True, "Loaded The File successfully."


def toggle_auto_refresh() -> bool:
    global config, auto_refresh_disabled

    auto_refresh_disabled = not auto_refresh_disabled

    config = save_config_sys({"disabled_auto_refresh": auto_refresh_disabled})

    logging.info(f"Auto refresh set disabled to: {auto_refresh_disabled}")

    return auto_refresh_disabled


def is_auto_refresh_disabled() -> bool:
    global auto_refresh_disabled
    return auto_refresh_disabled


def load_excel_lazy(path):
    global df_unfiltered, df_raw, df

    if not path:
        raise ValueError("Path cannot be empty.")

    is_exist = os.path.exists(path)

    if not is_exist:
        raise ValueError("The path does not exist.")

    df_unfiltered = pl.read_excel(path, sheet_name="Sheet1").lazy()

    df_raw = preprocess_df(df_unfiltered)

    df_unfiltered = df_raw.pipe(filter_retard).pipe(filter_tec)

    df = df_unfiltered

    logging.info(f"Excel file loaded and processed: {path}")


def preprocess_df(raw_df: pl.LazyFrame) -> pl.LazyFrame:
    return raw_df.with_columns(
        pl.col("CODE_DR").cast(pl.Int32).alias("CODE_DR")
    ).filter(pl.col("AT_RXP_AFFRT") != "AFFRT")


def get_df_unfiltered() -> Optional[pl.LazyFrame]:
    global df_unfiltered
    if df_unfiltered is None and path_to_excel:
        update_df_unfiltered()
    return df_unfiltered


def get_df() -> Optional[pl.LazyFrame]:
    global df
    if df is None:
        return None
    return df


def get_total_df() -> Optional[pl.LazyFrame]:
    global total_df

    return total_df


def get_count_df(
    segmentation: Optional[str], unit_segmentation: Optional[str], min_date, max_date
) -> Optional[pl.LazyFrame]:
    global df_raw
    start = end = None
    filter_list = []

    if min_date:
        start = (
            min_date
            if isinstance(min_date, date)
            else datetime.fromisoformat(min_date).date()
        )
        filter_list.append(pl.col(COL_NAME_DEPARTURE_DATETIME) >= start)
        logging.debug(f"Applying min_date filter: {start}")

    if max_date:
        end = (
            max_date
            if isinstance(max_date, date)
            else datetime.fromisoformat(max_date).date()
        )
        filter_list.append(pl.col(COL_NAME_DEPARTURE_DATETIME) <= end)
        logging.debug(f"Applying max_date filter: {end}")



    stmt = df_raw
    if filter_list:
        stmt = df_raw.filter(filter_list)
        logging.debug(f"Filtered df_raw with {len(filter_list)} filter(s).")


    if segmentation and unit_segmentation:

        min_segmentation = str(segmentation) + unit_segmentation
        max_segmentation = str(segmentation - 1) + unit_segmentation
        logging.debug(f"Applying segmentation truncation: min={min_segmentation}, max={max_segmentation}")

        stmt = (
            stmt.with_columns(
                pl.col(COL_NAME_DEPARTURE_DATETIME)
                .dt.truncate(min_segmentation)
                .alias(COL_NAME_WINDOW_TIME),
            )
            .group_by(COL_NAME_WINDOW_TIME)
            .agg(pl.len().alias(COL_NAME_TOTAL_COUNT))
            .with_columns(
                pl.col(COL_NAME_WINDOW_TIME)
                .dt.offset_by(max_segmentation)
                .alias(COL_NAME_WINDOW_TIME_MAX),
            )
        )

    else:

        if start:
            stmt_start = pl.lit(start)

        else:
            stmt_start = pl.col(COL_NAME_DEPARTURE_DATETIME).min()

        if end:
            stmt_end = pl.lit(end)
        else:
            stmt_end = pl.col(COL_NAME_DEPARTURE_DATETIME).max()

        stmt_start = stmt_start.alias(COL_NAME_WINDOW_TIME)
        stmt_end = stmt_end.alias(COL_NAME_WINDOW_TIME_MAX)

        stmt = stmt.select([stmt_start, stmt_end, pl.len().alias(COL_NAME_TOTAL_COUNT)])

    return stmt


def get_modification_time_cashed() -> str:
    global config

    modification_date = config.get("modification_date", None)

    if modification_date is None:
        logging.debug("Modification date not found in config; fetching latest modification time.")

        modification_date = get_latest_modification_time()

    if modification_date:
        modification_date = datetime.strptime(modification_date, "%Y-%m-%d %H:%M:%S")

    return modification_date


def get_latest_modification_time():
    global path_to_excel
    is_path_exists = path_exits()
    if not is_path_exists:
        return None
    latest_modification_timestamp = os.path.getmtime(path_to_excel)
    readable_time = datetime.fromtimestamp(latest_modification_timestamp)
    readable_time = readable_time.strftime("%Y-%m-%d %H:%M:%S")

    return readable_time


def get_min_max_date_raw_df() -> tuple:
    global df_raw

    min_max_date = df_raw.select(
        pl.col(COL_NAME_DEPARTURE_DATETIME).min().alias("min_date"),
        pl.col(COL_NAME_DEPARTURE_DATETIME).max().alias("max_date"),
    ).collect()
    logging.debug("Min and max dates from raw DataFrame: %s", min_max_date)

    return min_max_date["min_date"][0], min_max_date["max_date"][0]


# program

df_raw: pl.LazyFrame = None
df_unfiltered: pl.LazyFrame = None
df: pl.LazyFrame = None
total_df: pl.LazyFrame = None

if path_to_excel and path_to_excel.strip() != "":
    try:
        load_excel_lazy(path_to_excel)
        logging.info(f"Excel file loaded successfully from: {path_to_excel}")
    except Exception as e:
        logging.info(f"Warning: Could not load Excel file at startup: {e}")
        df_unfiltered = None
        df_raw = None
        df = None
else:
    logging.info("No Excel path configured. Please set a path in the Settings page.")
    df_unfiltered = None
    df_raw = None
    df = None

modification_date = get_modification_time_cashed()

store_excel = dcc.Store(id=ID_PATH_STORE, storage_type="local", data=path_to_excel)

store_latest_date_fetch = dcc.Store(
    id=ID_STORE_DATE_WATCHER, storage_type="local", data=modification_date
)

store_trigger_change = dcc.Store(id=ID_DATA_STORE_TRIGGER)

interval_watcher = dcc.Interval(
    id=ID_INTERVAL_WATCHER, interval=1000, disabled=auto_refresh_disabled
)

hookers = [store_excel, store_latest_date_fetch, interval_watcher, store_trigger_change]


def add_watch_file():
    return Input(ID_STORE_DATE_WATCHER, "data")


def add_watcher_for_data():
    return Input(ID_DATA_STORE_TRIGGER, "data")


def update_df_unfiltered():
    global path_to_excel
    logging.info("Updating unfiltered dataframe by reloading Excel file")
    load_excel_lazy(path_to_excel)


def update_df(filtred_df: pl.LazyFrame, filtered_total_df: pl.LazyFrame):
    global df, total_df
    logging.info("Updated DataFrame with new filtered data.")


    df = filtred_df
    total_df = filtered_total_df
    logging.info("Updated DataFrame with new data.")


def add_callbacks():

    @app.callback(
        # output
        Output(ID_INTERVAL_WATCHER, "disabled"),
        # input
        Input(ID_PATH_STORE, "data"),
    )
    def loaded_file(_):
        global auto_refresh_disabled

        is_path_correct = path_exits() and (not auto_refresh_disabled)

        logging.info(f"Setting interval watcher disabled to {not is_path_correct}")

        return not is_path_correct

    @app.callback(
        # output
        Output(ID_STORE_DATE_WATCHER, "data"),
        # input
        State(ID_STORE_DATE_WATCHER, "data"),
        Input(ID_INTERVAL_WATCHER, "n_intervals"),
    )
    def watch_file(date_latest_fetch, _):
        global path_to_excel
        logging.info("Watching file every second...")
        if not path_to_excel:
            logging.warning("No Excel file path configured during watch.")
            return dash.no_update
        try:
            latest_modification_time = get_latest_modification_time()

            if latest_modification_time != date_latest_fetch:
                logging.info("File changed, updating DataFrame...")
                update_df_unfiltered()
                modify_modification_date(latest_modification_time)
                return latest_modification_time

        except FileNotFoundError:
            logging.warning("Excel file not found during watch.")
        except Exception as e:
            logging.error(f"Error watching file: {e}", exc_info=True)
        return dash.no_update
