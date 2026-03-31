import polars as pl

from data_managers.excel_manager import COL_NAME_WINDOW_TIME, COL_NAME_WINDOW_TIME_MAX


COL_NAME_COUNT_FLIGHTS = "count of flights"
COL_NAME_SUBTYPE = "AC_SUBTYPE"
COL_NAME_PERCENTAGE_DELAY = "pct"
COL_NAME_CATEGORY_GT_15MIN = "delay_category_gt_15min"
COL_NAME_CATEGORY_GT_15MIN_COUNT = "delay_cat_count"
COL_NAME_CATEGORY_GT_15MIN_MEAN = "delay_cat_mean"
COL_NAME_PERCENTAGE = "pct_by_registrations"


COL_NAME_COUNT_PERIOD = "count_of_period"
COL_NAME_COUNT_FLIGHTS_REGISTRATION_PER_SUBTYPE = "count_of_flights_subtype"
COL_NAME_COUNT_FLIGHTS_AIRPORT_PER_SUBTYPE = "count_of_flights_airport"


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


def calculate_period_distribution(
    df: pl.LazyFrame | pl.DataFrame,
) -> pl.LazyFrame | pl.DataFrame:
    counts_df = (
        df.group_by([COL_NAME_WINDOW_TIME, COL_NAME_WINDOW_TIME_MAX])
        .agg(pl.len().alias(COL_NAME_COUNT_PERIOD))
        .sort(COL_NAME_WINDOW_TIME)
    )
    total = counts_df[COL_NAME_COUNT_PERIOD].sum()
    if total == 0:
        return pl.DataFrame(
            {
                COL_NAME_WINDOW_TIME: [],
                COL_NAME_COUNT_PERIOD: [],
                COL_NAME_PERCENTAGE_DELAY: [],
            }
        )
    return counts_df.with_columns(
        (pl.col(COL_NAME_COUNT_PERIOD) * 100 / total)
        .round(2)
        .alias(COL_NAME_PERCENTAGE_DELAY)
    )


def calculate_delay_pct(df: pl.LazyFrame | pl.DataFrame) -> pl.LazyFrame | pl.DataFrame:
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


def calculate_subtype_registration_pct(
    df: pl.LazyFrame | pl.DataFrame,
) -> pl.LazyFrame | pl.DataFrame:
    # Step 1: group by subtype and registration
    grouped = df.group_by(
        [
            COL_NAME_WINDOW_TIME,
            COL_NAME_WINDOW_TIME_MAX,
            COL_NAME_SUBTYPE,
            "AC_REGISTRATION",
        ]
    ).agg(pl.count().alias(COL_NAME_COUNT_FLIGHTS_REGISTRATION_PER_SUBTYPE))

    # Step 2: calculate percentage of each registration inside the subtype
    with_pct = grouped.with_columns(
        (
            pl.col(COL_NAME_COUNT_FLIGHTS_REGISTRATION_PER_SUBTYPE)
            * 100
            / pl.col(COL_NAME_COUNT_FLIGHTS_REGISTRATION_PER_SUBTYPE)
            .sum()
            .over([COL_NAME_SUBTYPE, COL_NAME_WINDOW_TIME])
        )
        .round(2)
        .alias(COL_NAME_PERCENTAGE)
    )

    return with_pct.sort(
        [COL_NAME_SUBTYPE, COL_NAME_PERCENTAGE], descending=[False, True]
    )


def calculate_subtype_airport_pct(
    df: pl.LazyFrame | pl.DataFrame,
) -> pl.LazyFrame | pl.DataFrame:
    # Step 1: group by subtype and scheduled departure airport
    grouped = df.group_by(
        [
            COL_NAME_WINDOW_TIME,
            COL_NAME_WINDOW_TIME_MAX,
            COL_NAME_SUBTYPE,
            "DEP_AP_SCHED",
        ]
    ).agg(pl.count().alias(COL_NAME_COUNT_FLIGHTS_AIRPORT_PER_SUBTYPE))

    # Step 2: calculate percentage of each airport inside the subtype
    with_pct = grouped.with_columns(
        (
            pl.col(COL_NAME_COUNT_FLIGHTS_AIRPORT_PER_SUBTYPE)
            * 100
            / pl.col(COL_NAME_COUNT_FLIGHTS_AIRPORT_PER_SUBTYPE)
            .sum()
            .over([COL_NAME_WINDOW_TIME, COL_NAME_SUBTYPE])
        )
        .round(2)
        .alias(COL_NAME_PERCENTAGE)
    )

    return with_pct.sort(
        [COL_NAME_SUBTYPE, COL_NAME_PERCENTAGE], descending=[False, True]
    )
