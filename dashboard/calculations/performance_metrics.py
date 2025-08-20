from typing import Optional

from server_instance import get_app
import polars as pl

from data_managers.excel_manager import (
    get_df,
    COL_NAME_TOTAL_COUNT,
    COL_NAME_WINDOW_TIME,
    get_total_df,
)


COL_NAME_TOTAL_COUNT_FLIGHT_WITH_DELAY = "flight_with_delay"
COL_NAME_TOTAL_COUNT_FLIGHT_WITH_DELAY_GTE_15MIN = "flight_with_delay_gte_15min"
COL_NAME_TOTAL_COUNT_FLIGHT_WITH_DELAY_41_46_GTE_15MIN = (
    "flight_with_delay_gte_15min_code_41_46"
)


COL_NAME_PER_FLIGHTS_NOT_DELAYED = "per_flights_not_delayed"
COL_NAME_PER_DELAYED_FLIGHTS_NOT_WITH_15MIN = "per_delayed_flights_not_with_15min"
COL_NAME_PER_DELAYED_FLIGHTS_15MIN_NOT_WITH_41_46 = (
    "per_delayed_flights_15min__not_with_41_46"
)


ID_GRAPH_DELAY = "graph_delay_metrics"
ID_GRAPH_DELAY_15MIN = "graph_delay_15min_metrics"
ID_GRAPH_DELAY_41_46_15MIN = "graph_delay_41_46_15min_metrics"

ID_CARD_DELAY = "card_delay_metrics"
ID_CARD_DELAY_15MIN = "card_delay_15min_metrics"
ID_CARD_DELAY_15MIN_41_46 = "card_delay_15min_41_46_metrics"


app = get_app()


def calculate_graph_info_with_period(df: pl.LazyFrame) -> pl.LazyFrame:

    assert df is not None
    ##

    delayed_flights_count_df = df.group_by(COL_NAME_WINDOW_TIME).agg(
        pl.len().alias(COL_NAME_TOTAL_COUNT_FLIGHT_WITH_DELAY)
    )

    delayed_15min_df = df.filter((pl.col("DELAY_TIME") > 15))

    ##
    delayed_15min_count_df = delayed_15min_df.group_by(COL_NAME_WINDOW_TIME).agg(
        pl.len().alias(COL_NAME_TOTAL_COUNT_FLIGHT_WITH_DELAY_GTE_15MIN)
    )

    ##
    delayed_flights_41_46_gte_15min_count_df = (
        delayed_15min_df.filter(pl.col("DELAY_CODE").is_in({41, 46}))
        .group_by(COL_NAME_WINDOW_TIME)
        .agg(pl.len().alias(COL_NAME_TOTAL_COUNT_FLIGHT_WITH_DELAY_41_46_GTE_15MIN))
    )

    total_df = get_total_df()

    joined_df = (
        total_df.join(delayed_flights_count_df, COL_NAME_WINDOW_TIME, how="left")
        .join(delayed_15min_count_df, COL_NAME_WINDOW_TIME, how="left")
        .join(
            delayed_flights_41_46_gte_15min_count_df,
            COL_NAME_WINDOW_TIME,
            how="left",
        )
    )

    joined_df = joined_df.sort(COL_NAME_WINDOW_TIME)

    joined_df = joined_df.with_columns(
        [
            ## delay
            pl.lit(1)
            .sub(
                pl.col(COL_NAME_TOTAL_COUNT_FLIGHT_WITH_DELAY)
                / (pl.col(COL_NAME_TOTAL_COUNT))
            )
            .mul(100)
            .round(2)
            .alias(COL_NAME_PER_FLIGHTS_NOT_DELAYED),
            ## delay > 15
            pl.lit(1)
            .sub(
                pl.col(COL_NAME_TOTAL_COUNT_FLIGHT_WITH_DELAY_GTE_15MIN)
                / (pl.col(COL_NAME_TOTAL_COUNT))
            )
            .mul(100)
            .round(2)
            .alias(COL_NAME_PER_DELAYED_FLIGHTS_NOT_WITH_15MIN),
            ## delay > 15 min for 41 42
            pl.lit(1)
            .sub(
                (
                    pl.col(COL_NAME_TOTAL_COUNT_FLIGHT_WITH_DELAY_41_46_GTE_15MIN)
                    / pl.col(COL_NAME_TOTAL_COUNT)
                )
            )
            .mul(100)
            .round(2)
            .alias(COL_NAME_PER_DELAYED_FLIGHTS_15MIN_NOT_WITH_41_46),
        ]
    )

    return joined_df


def calculate_result() -> Optional[pl.DataFrame]:

    df = get_df()

    if df is None:
        return None

    df = calculate_graph_info_with_period(df)

    return df.collect()
