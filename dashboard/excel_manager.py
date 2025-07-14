import os
from typing import Optional
import polars as pl


from config import get_config_dir, config, load_config, save_config

from os.path import exists

# init

name_config = config.get("config", {}).get("config_data_name", "config_data.toml")

dir_main_config = get_config_dir()

path_config = os.path.join(dir_main_config, name_config)


config = load_config(path_config)


path_to_excel = config.get("path_to_excel", "")


# func


def path_exits():
    global path_to_excel

    return bool(path_to_excel)


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

    is_exist = exists(path)

    if is_exist:
        config["path_to_excel"] = path
        path_to_excel = path

        load_excel_lazy(path)

        save_config(path_config, config)
        return True, "Loaded The File successfully."
    return is_exist, "The excel file doesn't exists."


def load_excel_lazy(path) -> Optional[pl.LazyFrame]:

    if not path:
        return None

    is_exist = exists(path)

    if not is_exist:
        return None

    res = pl.read_excel(path, sheet_name="Sheet1").lazy()

    res = filter_tec(res)

    return res


def get_df() -> Optional[pl.LazyFrame]:
    return df


# program


df = load_excel_lazy(path_to_excel)
