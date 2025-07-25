import datetime
import os
from typing import Optional
import dash
import polars as pl

from dash import Input, Output, State, dcc


from config import get_config_dir, config, load_config, save_config
from server_instance import get_app


# global


ID_PATH_STORE = "is-path-store"
ID_INTERVAL_WATCHER = "interval-file-selector"

ID_STORE_DATE_WATCHER = "store-date-latest-fetch"


COL_NAME_DEPARTURE_DATETIME = "DEP_DAY_SCHED"

COL_NAME_WINDOW_TIME = "WINDOW_DATETIME_DEP"
COL_NAME_TOTAL_COUNT = "total_count"


ID_DATA_STORE_TRIGGER = "filter-store-trigger"


DEFAULT_WINDOW_SEGMENTATION = "All Period"

# init


app = get_app()


name_config = config.get("config", {}).get("config_data_name", "config_data.toml")

dir_main_config = get_config_dir()

path_config = os.path.join(dir_main_config, name_config)


config = load_config(path_config)


path_to_excel = config.get("path_to_excel", "")
auto_refresh = config.get("auto_refresh", True)


count_excel_lazy = None
# func


def get_path_to_excel():

    return path_to_excel


def path_exits():

    if not path_to_excel:
        return False

    is_exist = os.path.exists(path_to_excel)
    if not is_exist:
        return False

    is_file = os.path.isfile(path_to_excel)

    if not is_file:
        return False

    return True


def filter_tec(df_lazy: pl.LazyFrame) -> pl.LazyFrame:

    return df_lazy.filter(
        pl.col("CODE_DR").is_in([41, 42, 43, 44, 45, 46, 47, 51, 52, 55, 56, 57])
    )


def filter_retard(df_lazy: pl.LazyFrame) -> pl.LazyFrame:
    return df_lazy.filter(pl.col("Retard en min") != 0)


def create_dep_datetime(df_lazy: pl.LazyFrame) -> pl.LazyFrame:
    return df_lazy.with_columns(
        pl.col("DEP_DAY_SCHED")
        .dt.combine(pl.col("DEP_TIME_SCHED").str.strptime(pl.Time, "%H:%M"))
        .alias(COL_NAME_DEPARTURE_DATETIME)
    )


def modify_modification_date(new_modification_date: float):
    global config, modification_date

    modification_date = new_modification_date
    config["modification_date"] = new_modification_date

    save_config(path_config, config)

    print(f"Set modification date to to: {new_modification_date}")
    save_config(path_config, config)


def update_path_to_excel(path) -> tuple[bool, str]:
    global config, path_to_excel

    if not path:
        return False, "Path cannot be empty."

    is_exist = os.path.exists(path)
    if not is_exist:
        return is_exist, "The excel file doesn't exists."

    is_file = os.path.isfile(path)

    if not is_file:
        return (
            False,
            "The Path you provided is not for a file make sure it ends with '.excel' or any other valid format for excel.",
        )

    try:
        load_excel_lazy(path)
    except:
        return False, "Could not load the file, make sure it is a valid excel file."

    path_to_excel = path
    config["path_to_excel"] = path

    save_config(path_config, config)

    return True, "Loaded The File successfully."


def toggle_auto_refresh() -> bool:
    global config, auto_refresh

    auto_refresh = not auto_refresh
    config["auto_refresh"] = auto_refresh

    save_config(path_config, config)

    print(f"Auto refresh set disabled to: {auto_refresh}")

    return auto_refresh


def is_auto_refresh_enabled() -> bool:
    global auto_refresh
    return auto_refresh


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


def preprocess_df(raw_df: pl.LazyFrame) -> pl.LazyFrame:
    return raw_df.with_columns(pl.col("CODE_DR").cast(pl.Int32).alias("CODE_DR"))


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


def get_count_df(segmentation: Optional[str]) -> Optional[pl.LazyFrame]:
    global df_raw

    if segmentation:
        stmt = (
            df_raw.with_columns(
                pl.col(COL_NAME_DEPARTURE_DATETIME)
                .dt.truncate(segmentation)
                .alias(COL_NAME_WINDOW_TIME)
            )
            .group_by(COL_NAME_WINDOW_TIME)
            .agg(pl.len().alias(COL_NAME_TOTAL_COUNT))
        )

    else:
        stmt = df_raw.select(
            [
                pl.lit(DEFAULT_WINDOW_SEGMENTATION).alias(COL_NAME_WINDOW_TIME),
                pl.count().alias(COL_NAME_TOTAL_COUNT),
            ]
        )
    return stmt


def get_latest_modification_time():
    global path_to_excel
    is_path_exists = path_exits()
    if not is_path_exists:
        return None
    latest_modification_timestamp = os.path.getmtime(path_to_excel)
    readable_time = datetime.datetime.fromtimestamp(
        latest_modification_timestamp
    ).isoformat()

    return readable_time


# program

df_raw: pl.LazyFrame = None
df_unfiltered: pl.LazyFrame = None
df: pl.LazyFrame = None
total_df: pl.LazyFrame = None

get_df


load_excel_lazy(path_to_excel)

modification_date = config.get("modification_date", get_latest_modification_time())


store_excel = dcc.Store(id=ID_PATH_STORE, storage_type="local", data=path_to_excel)


store_latest_date_fetch = dcc.Store(
    id=ID_STORE_DATE_WATCHER, storage_type="local", data=modification_date
)

store_trigger_change = dcc.Store(id=ID_DATA_STORE_TRIGGER)

interval_watcher = dcc.Interval(
    id=ID_INTERVAL_WATCHER, interval=1000, disabled=not auto_refresh
)


hookers = [store_excel, store_latest_date_fetch, interval_watcher, store_trigger_change]


def add_watch_file():
    return Input(ID_STORE_DATE_WATCHER, "data")


def add_watcher_for_data():
    return Input(ID_DATA_STORE_TRIGGER, "data")


def update_df_unfiltered():

    load_excel_lazy(path_to_excel)


def update_df(filtred_df: pl.LazyFrame, filtered_total_df: pl.LazyFrame):
    global df, total_df

    df = filtred_df
    total_df = filtered_total_df
    print("Updated DataFrame with new data.")


def add_callbacks():

    @app.callback(
        # output
        Output(ID_INTERVAL_WATCHER, "disabled"),
        # input
        Input(ID_PATH_STORE, "data"),
    )
    def loaded_file(_):
        global auto_refresh, config

        is_path_correct = not (path_exits() and auto_refresh)

        print(f"Setting interval watcher disabled to {is_path_correct}")

        return is_path_correct

    @app.callback(
        # output
        Output(ID_STORE_DATE_WATCHER, "data"),
        # input
        State(ID_STORE_DATE_WATCHER, "data"),
        Input(ID_INTERVAL_WATCHER, "n_intervals"),
    )
    def watch_file(date_latest_fetch, _):
        global path_to_excel

        if not path_to_excel:
            return dash.no_update
        try:
            latest_modification_time = get_latest_modification_time()

            if latest_modification_time != date_latest_fetch:
                print(
                    "File changed old : ",
                    date_latest_fetch,
                    ", new: ",
                    latest_modification_time,
                )

                update_df_unfiltered()
                modify_modification_date(latest_modification_time)
                return latest_modification_time

        except FileNotFoundError:
            print("not found")
        except Exception as e:
            print(f"Error watching file: {e}")

        return dash.no_update
