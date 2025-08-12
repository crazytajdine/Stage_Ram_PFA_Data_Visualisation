from datetime import datetime, date
import os
from typing import Optional
import dash
import polars as pl
import logging

from dash import Input, Output, State, dcc

from configurations.config import get_base_config, get_user_config, save_config_sys
from schemas.data_status import StatusData
from server_instance import get_app

from status.data_status_manager import compare_status, set_status

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
ID_DATA_STATUS_CHANGE_TRIGGER = "store-status-data-trigger"

# init

app = get_app()

base_config = get_base_config()
config = get_user_config()

dir_path = base_config.get("dir_path", "")
path_to_excel_cashed = config.get("path_to_excel", "")

# func


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


def get_path_to_excel() -> str:
    global dir_path, path_to_excel_cashed, config

    if path_to_excel_cashed:
        is_exist = os.path.exists(path_to_excel_cashed)

        if is_exist:
            logging.debug(f"Using cached Excel path: {path_to_excel_cashed}")
            return path_to_excel_cashed
        else:
            config = save_config_sys({"path_to_excel": ""})
            path_to_excel_cashed = ""

            logging.debug(f"Cashed path doesn't exist : {path_to_excel_cashed}")

    logging.info(f"Scanning directory: {dir_path}")

    os.makedirs(dir_path, exist_ok=True)

    try:
        list_name_excels: list[str] = os.listdir(dir_path)
        logging.info(f"Found files: {list_name_excels}")
    except Exception as e:
        logging.error(f"Error reading directory: {e}")
        return None
    list_name_excels = [
        name
        for name in list_name_excels
        if (name.endswith(".xlsx") or name.endswith(".xls"))
        and (not name.startswith("~$"))
    ]

    logging.info(f"Filtered Excel files: {list_name_excels}")

    if not list_name_excels:
        logging.warning("No Excel files found in the directory.")
        return None

    first_excel = list_name_excels[0]
    full_path = os.path.join(dir_path, first_excel)

    config = save_config_sys({"path_to_excel": full_path})
    path_to_excel_cashed = full_path
    logging.info(f"Selected Excel file: {full_path}")

    return full_path


def filter_tec(df_lazy: pl.LazyFrame) -> pl.LazyFrame:
    logging.info("Filtering technical delay codes from dataframe")
    try:
        filtered_df = df_lazy.filter(
            pl.col("DELAY_CODE").is_in([41, 42, 43, 44, 45, 46, 47, 51, 52])
        )
        logging.debug("Filter applied on CODE_DR for technical delays")
        return filtered_df
    except Exception as e:
        logging.error(f"Error filtering technical delay codes: {e}", exc_info=True)
        return df_lazy


def filter_retard(df_lazy: pl.LazyFrame) -> pl.LazyFrame:
    logging.info("Filtering rows where 'Retard en min' is not zero")
    try:
        filtered_df = df_lazy.filter(pl.col("DELAY_TIME") != 0)
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
        logging.debug(
            f"Added column '{COL_NAME_DEPARTURE_DATETIME}' combining date and time"
        )
        return df_with_datetime
    except Exception as e:
        logging.error(f"Error creating departure datetime: {e}", exc_info=True)
        return df_lazy


def load_excel_lazy(path_to_excel):
    global df_unfiltered, df_raw, df

    path_to_excel = get_path_to_excel()
    if not path_to_excel:
        return None

    df_read = pl.read_excel(path_to_excel).lazy()

    df_raw = preprocess_df(df_read)

    df_unfiltered = df_raw.pipe(filter_retard).pipe(filter_tec)

    df = df_unfiltered

    logging.info(f"Excel file loaded and processed: {path_to_excel}")


def preprocess_df(raw_df: pl.LazyFrame) -> pl.LazyFrame:
    return raw_df.with_columns(
        pl.col("DELAY_CODE").cast(pl.Int32).alias("DELAY_CODE")
    ).filter(pl.col("AC_REGISTRATION").str.starts_with("CN"))


def get_df_unfiltered() -> Optional[pl.LazyFrame]:
    global df_unfiltered

    path_excel = get_path_to_excel()
    if df_unfiltered is None and path_excel:
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
        logging.debug(
            f"Applying segmentation truncation: min={min_segmentation}, max={max_segmentation}"
        )

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
        logging.debug(
            "Modification date not found in config; fetching latest modification time."
        )

        modification_date = get_latest_modification_time()

    if modification_date:
        modification_date = datetime.strptime(modification_date, "%Y-%m-%d %H:%M:%S")

    return modification_date


def path_exists():

    path_excel = get_path_to_excel()
    does_path_exists = bool(path_excel)
    logging.info(f"Verifying if cashed path exists got : {does_path_exists}")
    return does_path_exists


def get_latest_modification_time():

    path_excel = get_path_to_excel()
    if not path_excel:
        return None
    latest_modification_timestamp = os.path.getmtime(path_excel)
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

path_to_excel = get_path_to_excel()
if path_to_excel and path_to_excel.strip() != "":
    try:
        load_excel_lazy(path_to_excel)
        logging.info(f"Excel file loaded successfully from: {path_to_excel}")
    except Exception as e:
        logging.info(f"Warning: Could not load Excel file at startup: {e}")
        path_to_excel_cashed = ""
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
store_trigger_status = dcc.Store(ID_DATA_STATUS_CHANGE_TRIGGER)
interval_watcher = dcc.Interval(id=ID_INTERVAL_WATCHER, interval=1000)

hookers = [
    store_excel,
    store_latest_date_fetch,
    interval_watcher,
    store_trigger_change,
    store_trigger_status,
]


def add_watch_file():
    return Input(ID_STORE_DATE_WATCHER, "data")


def add_watcher_for_data_status():
    return Input(ID_DATA_STATUS_CHANGE_TRIGGER, "data")


def add_watcher_for_data():
    return Input(ID_DATA_STORE_TRIGGER, "data")


def update_df_unfiltered():
    global path_to_excel_cashed
    logging.info("Updating unfiltered dataframe by reloading Excel file")
    try:
        load_excel_lazy(get_path_to_excel())
    except Exception:
        path_to_excel_cashed = ""
        logging.info(f"Warning: Could not load Excel file at startup: {e}")


def modify_modification_date(new_modification_date: float):
    global config

    config = save_config_sys({"modification_date": new_modification_date})

    logging.info(f"Set modification date to: {new_modification_date}")


def update_df(filtred_df: pl.LazyFrame, filtered_total_df: pl.LazyFrame):
    global df, total_df
    logging.info("Updated DataFrame with new filtered data.")

    df = filtred_df
    total_df = filtered_total_df
    logging.info("Updated DataFrame with new data.")


def add_callbacks():

    @app.callback(
        Output(ID_STORE_DATE_WATCHER, "data", allow_duplicate=True),
        Output(ID_DATA_STORE_TRIGGER, "data", allow_duplicate=True),
        Input(ID_PATH_STORE, "data"),
        prevent_initial_call=True,
    )
    def trigger_data_path_change(_):
        return None, None

    @app.callback(
        Output(ID_DATA_STATUS_CHANGE_TRIGGER, "data"),
        Input(ID_PATH_STORE, "data"),
    )
    def trigger_data_status_change(_):

        logging.info("Data status changed.")
        new_status: StatusData = "selected" if path_exists() else "unselected"

        same_as_old_status = compare_status(new_status)
        set_status(new_status)

        logging.info(
            f"sending status change: {new_status}, same as old: {same_as_old_status}"
        )
        return dash.no_update if same_as_old_status else None
