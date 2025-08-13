import polars as pl

from data_managers.cache_manager import cache_result
from data_managers.excel_manager import COL_NAME_WINDOW_TIME, COL_NAME_WINDOW_TIME_MAX


COL_NAME_COUNT_FLIGHTS = "count of flights"
COL_NAME_SUBTYPE = "AC_SUBTYPE"
COL_NAME_PERCENTAGE_DELAY = "pct"
COL_NAME_CATEGORY_GT_15MIN = "delay_category_gt_15min"
COL_NAME_CATEGORY_GT_15MIN_COUNT = "delay_cat_count"
COL_NAME_CATEGORY_GT_15MIN_MEAN = "delay_cat_mean"


# @cache_result("main_subtype_pct")
# def process_subtype_pct_data(df: pl.LazyFrame) -> pl.LazyFrame:
#     counts = df.group_by("AC_SUBTYPE").agg(pl.count().alias(COL_NAME_COUNT_FLIGHTS))

#     result = counts.with_columns(
#         [
#             (pl.col(COL_NAME_COUNT_FLIGHTS) * 100 / pl.sum(COL_NAME_COUNT_FLIGHTS))
#             .round(2)
#             .alias(COL_NAME_PERCENTAGE_DELAY)
#         ]
#     )

#     return result.sort(COL_NAME_PERCENTAGE_DELAY, descending=False)


def process_subtype_pct_data(df: pl.LazyFrame) -> pl.LazyFrame:
    # Step 1: group by window and subtype
    grouped = df.group_by(
        [COL_NAME_WINDOW_TIME, COL_NAME_WINDOW_TIME_MAX, "AC_SUBTYPE"]
    ).agg(pl.count().alias(COL_NAME_COUNT_FLIGHTS))

    # Step 2: calculate the percentage by window
    result = grouped.with_columns(
        (
            pl.col(COL_NAME_COUNT_FLIGHTS)
            * 100
            / pl.col(COL_NAME_COUNT_FLIGHTS)
            .sum()
            .over([COL_NAME_WINDOW_TIME, COL_NAME_WINDOW_TIME_MAX])
        )
        .round(2)
        .alias(COL_NAME_PERCENTAGE_DELAY)
    )

    return result.sort(COL_NAME_WINDOW_TIME)


@cache_result("main_period_distribution")
def calculate_period_distribution(df: pl.DataFrame) -> pl.DataFrame:
    counts_df = (
        df.group_by([COL_NAME_WINDOW_TIME, COL_NAME_WINDOW_TIME_MAX])
        .agg(pl.len().alias("count"))
        .sort(COL_NAME_WINDOW_TIME)
    )
    total = counts_df["count"].sum()
    if total == 0:
        return pl.DataFrame(
            {
                COL_NAME_WINDOW_TIME: [],
                "count": [],
                COL_NAME_PERCENTAGE_DELAY: [],
            }
        )
    return counts_df.with_columns(
        (pl.col("count") * 100 / total).round(2).alias(COL_NAME_PERCENTAGE_DELAY)
    )


@cache_result("main_delay_pct")
def calculate_delay_pct(df: pl.LazyFrame) -> pl.LazyFrame:
    # 1) Categorize delays
    df = df.with_columns(
        pl.when(pl.col("DELAY_TIME") > 15)
        .then(pl.lit("flights with delay > 15 min"))
        .otherwise(pl.lit("flights with delay ≤ 15 min"))
        .alias(COL_NAME_CATEGORY_GT_15MIN)
    )

    # 2) Group by time window and delay category
    res = df.group_by(
        [COL_NAME_WINDOW_TIME, COL_NAME_WINDOW_TIME_MAX, COL_NAME_CATEGORY_GT_15MIN]
    ).agg(pl.count().alias(COL_NAME_CATEGORY_GT_15MIN_COUNT))

    # 3) Compute percentage per time window
    res = res.with_columns(
        (
            pl.col(COL_NAME_CATEGORY_GT_15MIN_COUNT)
            * 100
            / pl.col(COL_NAME_CATEGORY_GT_15MIN_COUNT)
            .sum()
            .over([COL_NAME_WINDOW_TIME, COL_NAME_WINDOW_TIME_MAX])
        )
        .round(2)
        .alias(COL_NAME_CATEGORY_GT_15MIN_MEAN)
    )

    return res
