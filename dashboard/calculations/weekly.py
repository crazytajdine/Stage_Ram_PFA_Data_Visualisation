from typing import List, Optional, Tuple
import polars as pl

# ─────────────── Application modules ───────────────
from data_managers.cache_manager import cache_result
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


@cache_result("weekly_codes_analysis")
def analyze_weekly_codes() -> Tuple[Optional[pl.DataFrame], List[str]]:
    df_lazy = get_df()
    if df_lazy is None:
        return None, []

    df = (
        df_lazy.sort("DEP_DAY_SCHED")
        .with_columns(
            pl.col("DEP_DAY_SCHED").dt.strftime("%A").alias("DAY_OF_WEEK_DEP")
        )
        .collect()
    )

    if df.is_empty():
        return None

    # Group and pivot
    pivot: pl.DataFrame = (
        df.group_by(["DELAY_CODE", "DAY_OF_WEEK_DEP"])
        .agg(pl.len().alias("n"))
        .pivot(values="n", index="DELAY_CODE", columns="DAY_OF_WEEK_DEP")
        .fill_null(0)
    )

    # compute day columns (all except DELAY_CODE) and add Total (sum across day columns)
    day_cols = [c for c in weekday_order if c in pivot.columns]
    pivot = (
        pivot.select("DELAY_CODE", *day_cols)
        .with_columns(pl.sum_horizontal(day_cols).alias("Total"))
        .sort("Total", descending=True)
    )

    percent_cols = [
        (pl.col(c) / pl.col("Total") * 100)
        .round(2)
        .alias(COL_NAME_DATE_PERCENTAGE.format(c=c))
        for c in day_cols
    ]

    pivot_pct = pivot.with_columns(percent_cols)

    return pivot_pct, day_cols
