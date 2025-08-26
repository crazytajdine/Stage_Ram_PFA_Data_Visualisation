from data_managers.excel_manager import (
    COL_NAME_WINDOW_TIME,
    COL_NAME_WINDOW_TIME_MAX,
    get_df,
)

import polars as pl

COL_NAME_COUNT_DELAY_FAMILY = "count_delay_family"
COL_NAME_COUNT_DELAY_PER_CODE_DELAY_PER_FAMILY = "count_delay_per_code_delay_per_family"
COL_NAME_PERCENTAGE_FAMILY_PER_PERIOD = "perc_family_per_period"
COL_NAME_PERCENTAGE_DELAY_CODE_PER_FAMILY_PER_PERIOD = "perc_family"
COL_NAME_PERCENTAGE_DELAY_CODE_PER_FAMILY_PER_PERIOD_TOTAL = "perc_family_total"
COL_NAME_PERCENTAGE_SUBTYPE_FAMILY = "pct_subtype_family_vs_family_total"
COL_NAME_PERCENTAGE_REGISTRATION_FAMILY = "pct_registration_family_vs_family_total"
COL_NAME_SUBTYPE = "AC_SUBTYPE"


COL_NAME_COUNT_PER_REGISTRATION_FAMILY = "count_per_registration_family"
COL_NAME_COUNT_PER_SUBTYPE_FAMILY = "count_per_subtype_family"
COL_NAME_COUNT_FAMILY_TOTAL = "count_family_total"


def analyze_delay_codes_polars() -> pl.DataFrame:

    frame = get_df().collect()

    if frame.is_empty():
        return pl.DataFrame(
            {
                "DELAY_CODE": [],
                "Occurrences": [],
                "Description": [],
                "Aeroports": [],
                "Nb_AP": [],
            }
        )

    # First get airport counts per code
    airport_counts = frame.group_by(["DELAY_CODE", "DEP_AP_SCHED"]).agg(
        pl.len().alias("ap_count")
    )

    agg = (
        frame.group_by("DELAY_CODE")
        .agg(
            [
                pl.len().alias("Occurrences"),
                pl.col("LIB_CODE_DR").first().alias("Description"),
                pl.col("DEP_AP_SCHED").drop_nulls().alias("AP_list"),
            ]
        )
        .join(
            airport_counts.group_by("DELAY_CODE").agg(
                [
                    pl.col("DEP_AP_SCHED").alias("airports"),
                    pl.col("ap_count").alias("counts"),
                ]
            ),
            on="DELAY_CODE",
            how="left",
        )
        .with_columns(
            [
                pl.struct(["airports", "counts"])
                .map_elements(
                    lambda x: ", ".join(
                        [
                            f"{ap} ({cnt})"
                            for ap, cnt in sorted(
                                zip(x["airports"], x["counts"]),
                                key=lambda item: item[1],
                                reverse=True,
                            )
                        ]
                    ),
                    return_dtype=pl.Utf8,
                )
                .alias("Aeroports"),
                pl.col("AP_list").list.n_unique().alias("Nb_AP"),
            ]
        )
        .select(["DELAY_CODE", "Occurrences", "Description", "Aeroports", "Nb_AP"])
        .sort("Occurrences", descending=True)
    )
    return agg


def prepare_delay_data():
    df = get_df()
    if df is None:
        return None, None

    df = df.collect()

    # Count per family + delay code
    temporal_all = df.group_by([COL_NAME_WINDOW_TIME, "FAMILLE_DR", "DELAY_CODE"]).agg(
        pl.len().alias(COL_NAME_COUNT_DELAY_PER_CODE_DELAY_PER_FAMILY),
        pl.col(COL_NAME_WINDOW_TIME_MAX).first().alias(COL_NAME_WINDOW_TIME_MAX),
    )

    # Total per period
    period_totals = temporal_all.group_by(COL_NAME_WINDOW_TIME).agg(
        pl.col(COL_NAME_COUNT_DELAY_PER_CODE_DELAY_PER_FAMILY)
        .sum()
        .alias("period_total"),
    )

    # Total per family (per period)
    family_totals = temporal_all.group_by([COL_NAME_WINDOW_TIME, "FAMILLE_DR"]).agg(
        pl.col(COL_NAME_COUNT_DELAY_PER_CODE_DELAY_PER_FAMILY)
        .sum()
        .alias(COL_NAME_COUNT_FAMILY_TOTAL),
        pl.col(COL_NAME_WINDOW_TIME_MAX).first().alias(COL_NAME_WINDOW_TIME_MAX),
    )

    # Join totals

    temporal_all = (
        temporal_all.join(period_totals, on=COL_NAME_WINDOW_TIME)
        .join(family_totals, on=[COL_NAME_WINDOW_TIME, "FAMILLE_DR"])
        .with_columns(
            [
                # % vs total period
                (
                    pl.col(COL_NAME_COUNT_DELAY_PER_CODE_DELAY_PER_FAMILY)
                    / pl.col("period_total")
                    * 100
                )
                .round(2)
                .alias(COL_NAME_PERCENTAGE_DELAY_CODE_PER_FAMILY_PER_PERIOD_TOTAL),
                # % vs total family in same period
                (
                    pl.col(COL_NAME_COUNT_DELAY_PER_CODE_DELAY_PER_FAMILY)
                    / pl.col(COL_NAME_COUNT_FAMILY_TOTAL)
                    * 100
                )
                .round(2)
                .alias(COL_NAME_PERCENTAGE_DELAY_CODE_PER_FAMILY_PER_PERIOD),
            ]
        )
    )

    # Family share vs period
    famille_share_df = family_totals.join(
        period_totals, on=COL_NAME_WINDOW_TIME
    ).with_columns(
        (pl.col(COL_NAME_COUNT_FAMILY_TOTAL) / pl.col("period_total") * 100)
        .round(2)
        .alias(COL_NAME_PERCENTAGE_FAMILY_PER_PERIOD)
    )
    return (
        temporal_all,
        famille_share_df,
    )


def prepare_subtype_family_data():
    df = get_df().collect()
    # Count per FAMILLE_DR + AC_SUBTYPE per time window
    temporal_all = df.group_by([COL_NAME_WINDOW_TIME, "AC_SUBTYPE", "FAMILLE_DR"]).agg(
        pl.len().alias(COL_NAME_COUNT_PER_SUBTYPE_FAMILY),
        pl.col(COL_NAME_WINDOW_TIME_MAX).first().alias(COL_NAME_WINDOW_TIME_MAX),
    )

    # Total per period
    period_totals = temporal_all.group_by([COL_NAME_WINDOW_TIME, "AC_SUBTYPE"]).agg(
        pl.col(COL_NAME_COUNT_PER_SUBTYPE_FAMILY).sum().alias("period_total")
    )

    # Join totals and calculate percentages

    temporal_all = temporal_all.join(
        period_totals, on=[COL_NAME_WINDOW_TIME, "AC_SUBTYPE"]
    ).with_columns(
        [
            # % vs total period
            (pl.col(COL_NAME_COUNT_PER_SUBTYPE_FAMILY) / pl.col("period_total") * 100)
            .round(2)
            .alias(COL_NAME_PERCENTAGE_SUBTYPE_FAMILY),
        ]
    )

    return temporal_all


def prepare_registration_family_data():

    df = get_df().collect()

    # Count per FAMILLE_DR + AC_REGISTRATION per time window
    temporal_all = df.group_by(
        [COL_NAME_WINDOW_TIME, "AC_REGISTRATION", "FAMILLE_DR"]
    ).agg(
        pl.len().alias(COL_NAME_COUNT_PER_REGISTRATION_FAMILY),
        pl.col(COL_NAME_WINDOW_TIME_MAX).first().alias(COL_NAME_WINDOW_TIME_MAX),
    )

    # Total per period
    period_totals = temporal_all.group_by(
        [COL_NAME_WINDOW_TIME, "AC_REGISTRATION"]
    ).agg(pl.col(COL_NAME_COUNT_PER_REGISTRATION_FAMILY).sum().alias("period_total"))

    # Join totals and calculate percentages

    temporal_all = temporal_all.join(
        period_totals, on=[COL_NAME_WINDOW_TIME, "AC_REGISTRATION"]
    ).with_columns(
        [
            # % vs total period
            (
                pl.col(COL_NAME_COUNT_PER_REGISTRATION_FAMILY)
                / pl.col("period_total")
                * 100
            )
            .round(2)
            .alias(COL_NAME_PERCENTAGE_REGISTRATION_FAMILY),
        ]
    )

    return temporal_all
