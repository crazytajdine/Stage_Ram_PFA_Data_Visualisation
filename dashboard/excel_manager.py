import os
from typing import Optional
import polars as pl

from dash import dcc


from config import get_config_dir, config, load_config, save_config


# init

name_config = config.get("config", {}).get("config_data_name", "config_data.toml")

dir_main_config = get_config_dir()

path_config = os.path.join(dir_main_config, name_config)


config = load_config(path_config)


path_to_excel = config.get("path_to_excel", "")


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

    return df_lazy.filter(pl.col("LIB_CODE_DR") == "TEC")


def create_dep_datetime(df_lazy: pl.LazyFrame) -> pl.LazyFrame:
    return df_lazy.with_columns(
        pl.col("DEP_DAY_SCHED")
        .dt.combine(pl.col("DEP_TIME_SCHED").str.strptime(pl.Time, "%H:%M"))
        .alias("DEP_DATETIME")
    )


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
        return True, "."

    config["path_to_excel"] = path
    path_to_excel = path
    save_config(path_config, config)
    return True, "Loaded The File successfully."


def load_excel_lazy(path) -> Optional[pl.LazyFrame]:

    if not path:
        return None

    is_exist = os.path.exists(path)

    if not is_exist:
        return None

    res = pl.read_excel(path, sheet_name="Sheet1").lazy()

    res = res.pipe(filter_tec)

    return res


# @app.callback(
#     Output("data-store", "data"),
#     Input("path-store", "data"),
# )
# def load_data(path):

#     print("Loading data from:", path)

#     df = get_df()
#     if df is None:
#         return None

#     return df


def get_df() -> Optional[pl.LazyFrame]:
    return df


# program

store_excel = dcc.Store(id="is-path-store", storage_type="local", data=path_exits())


df = load_excel_lazy(path_to_excel)
