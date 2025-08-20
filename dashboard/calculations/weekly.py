from datetime import datetime
from typing import List, Optional, Tuple
import polars as pl

# ─────────────── Application modules ───────────────
from utils_dashboard.utils_filter import get_date_range
from data_managers.excel_manager import (
    get_df,
)

weekday_order = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]
COL_NAME_DATE_PERCENTAGE = "{c}_pct"


def get_weekday_range(start: datetime.date, end: datetime.date) -> List[str]:
    start_idx = start.weekday()

    days_between = (end - start).days
    if days_between < 6:
        range_difference = days_between + 1
    else:
        range_difference = 7
    return [weekday_order[(start_idx + i) % 7] for i in range(range_difference)]


def analyze_weekly_codes() -> Tuple[Optional[pl.DataFrame], List[str]]:
    df_lazy = get_df()
    if df_lazy is None:
        return None, []

    start_date, end_date = get_date_range()

    df = df_lazy.with_columns(
        pl.col("DEP_DAY_SCHED").dt.strftime("%A").alias("DAY_OF_WEEK_DEP")
    ).collect()

    if df.is_empty():
        return None, []

    # Group and pivot
    pivot: pl.DataFrame = (
        df.group_by(["DELAY_CODE", "DAY_OF_WEEK_DEP"])
        .agg(pl.len().alias("n"), pl.col("DEP_DAY_SCHED").min())
        .sort("DEP_DAY_SCHED")
        .pivot(values="n", index="DELAY_CODE", columns="DAY_OF_WEEK_DEP")
        .fill_null(0)
    )

    # ---- Reorder days according to the actual date range ----
    day_range = get_weekday_range(start_date, end_date)
    for day in day_range:
        if day not in pivot.columns:
            pivot = pivot.with_columns(pl.lit(0).alias(day))

    # Only keep the day_range (in order) + DELAY_CODE
    pivot = pivot.select(["DELAY_CODE", *day_range])

    # Add total
    pivot = pivot.with_columns(pl.sum_horizontal(day_range).alias("Total")).sort(
        "Total", descending=True
    )

    # Percentages
    percent_cols = [
        (pl.col(c) / pl.col("Total") * 100)
        .round(2)
        .alias(COL_NAME_DATE_PERCENTAGE.format(c=c))
        for c in day_range
    ]
    pivot_pct = pivot.with_columns(percent_cols)

    return pivot_pct, day_range
