from typing import Optional, Tuple
import dash
import polars as pl
from datetime import date, datetime
from dash import Input, Output, State
from excel_manager import (
    COL_NAME_DEPARTURE_DATETIME,
    COL_NAME_WINDOW_TIME,
    ID_DATA_STORE_TRIGGER,
    DEFAULT_WINDOW_SEGMENTATION,
    update_df,
    get_df_unfiltered,
    get_df,
    add_watch_file,
    get_count_df,
)
from server_instance import get_app
import dash_bootstrap_components as dbc

from dash import html, dcc

FILTER_SUBTYPE = "filter-subtype"
FILTER_MATRICULE = "filter-matricule"
FILTER_SEGMENTATION = "filter-segmentation"
FILTER_DATE_RANGE = "filter-date-range"
FILTER_SUBMIT_BTN = "filter-go-btn"
# FILTER_RESET_BTN = "filter-reset-btn"
FILTER_STORE_SUGGESTIONS = "filter-store-suggestions"
FILTER_STORE_ACTUAL = "filter-store-actual"

UNIT_SEGMENTATION = "d"


app = get_app()


layout = dbc.Card(
    dbc.CardBody(
        [
            dcc.Store(id=FILTER_STORE_SUGGESTIONS),
            dcc.Store(id=FILTER_STORE_ACTUAL),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Label("Type d'avion (Flotte)"),
                            dcc.Dropdown(
                                id=FILTER_SUBTYPE,
                                options=[],
                                multi=True,
                                placeholder="Tous les types",
                            ),
                        ],
                        md=6,
                    ),
                    dbc.Col(
                        [
                            html.Label("Matricule"),
                            dcc.Dropdown(
                                id=FILTER_MATRICULE,
                                options=[],
                                multi=True,
                                placeholder="Tous les matricules",
                            ),
                        ],
                        md=6,
                    ),
                ],
                className="mb-3",
            ),
            # segmentation
            dbc.Row(
                dbc.Col(
                    [
                        html.Label("Segmentation"),
                        dbc.Input(
                            id=FILTER_SEGMENTATION,
                            placeholder="Select segmentation (days)",
                            type="number",
                            max=5,
                        ),
                    ]
                ),
                className="mb-3",
            ),
            # dates
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Label("Date :"),
                            dcc.DatePickerRange(
                                id=FILTER_DATE_RANGE,
                                clearable=True,
                            ),
                        ],
                        md=6,
                    ),
                ],
                className="mb-3",
            ),
            # analyse btn
            dbc.Row(
                dbc.Col(
                    [
                        dbc.Button(
                            "Analyser",
                            id=FILTER_SUBMIT_BTN,
                            color="primary",
                            className="w-100",
                            size="lg",
                        ),
                        # dbc.Button(
                        #     "Reset",
                        #     id=FILTER_RESET_BTN,
                        #     color="secondary",
                        #     className="w-100",
                        #     size="lg",
                        # ),
                    ]
                )
            ),
        ]
    ),
    className="m-4",
)


def apply_filters(
    df: pl.LazyFrame, filters: dict
) -> Tuple[pl.LazyFrame, Optional[pl.LazyFrame]]:

    segmentation = filters.get("fl_segmentation") if filters else None
    total_df = get_count_df(segmentation)

    if not filters:
        df = df.with_columns(
            pl.lit(DEFAULT_WINDOW_SEGMENTATION).alias(COL_NAME_WINDOW_TIME)
        )

        return df, total_df

    # Filter by AC_SUBTYPE
    if filters.get("fl_subtype"):
        df = df.filter(pl.col("AC_SUBTYPE").is_in(filters["fl_subtype"]))

    # Filter by AC_REGISTRATION
    if filters.get("fl_matricule"):
        df = df.filter(pl.col("AC_REGISTRATION").is_in(filters["fl_matricule"]))

    # Filter by SEGMENTATION
    if segmentation := filters.get("fl_segmentation"):

        df = df.with_columns(
            pl.col(COL_NAME_DEPARTURE_DATETIME)
            .dt.truncate(segmentation)
            .alias(COL_NAME_WINDOW_TIME)
        )

    else:
        df = df.with_columns(
            pl.lit(DEFAULT_WINDOW_SEGMENTATION).alias(COL_NAME_WINDOW_TIME)
        )

    # Filter by date range (DEP_DAY_SCHED)
    if filters.get("dt_start"):
        # allow ISO‐string or date
        start = (
            filters["dt_start"]
            if isinstance(filters["dt_start"], date)
            else datetime.fromisoformat(filters["dt_start"]).date()
        )
        df = df.filter(pl.col(COL_NAME_DEPARTURE_DATETIME) >= start)

    if filters.get("dt_end"):
        end = (
            filters["dt_end"]
            if isinstance(filters["dt_end"], date)
            else datetime.fromisoformat(filters["dt_end"]).date()
        )
        df = df.filter(pl.col(COL_NAME_DEPARTURE_DATETIME) <= end)

    return df, total_df


def split_views_by_exclusion(
    df: pl.LazyFrame, filters: dict
) -> tuple[pl.LazyFrame, pl.LazyFrame, pl.LazyFrame]:

    f1 = {**filters, "fl_subtype": None}
    print(f1)
    view_subtype, _ = apply_filters(df, f1)

    # exclude matricule
    f2 = {**filters, "fl_matricule": None}
    view_matricule, _ = apply_filters(df, f2)

    # exclude both dates
    f3 = {**filters, "dt_start": None, "dt_end": None}
    view_date, _ = apply_filters(df, f3)

    return view_subtype, view_matricule, view_date


@app.callback(
    Output(FILTER_SUBTYPE, "options"),
    Output(FILTER_MATRICULE, "options"),
    Output(FILTER_DATE_RANGE, "min_date_allowed"),
    Output(FILTER_DATE_RANGE, "max_date_allowed"),
    Input(FILTER_STORE_SUGGESTIONS, "data"),
)
def update_filter_options(store_data):

    base_lazy = get_df_unfiltered()  # your global LazyFrame

    v_sub, v_mat, v_date = split_views_by_exclusion(base_lazy, store_data)

    # subtype dropdown
    df_sub = v_sub.collect()
    subtypes = sorted(df_sub.get_column("AC_SUBTYPE").drop_nulls().unique().to_list())

    # matricule dropdown
    df_mat = v_mat.collect()
    matricules = sorted(
        df_mat.get_column("AC_REGISTRATION").drop_nulls().unique().to_list()
    )

    # date bounds
    df_dt = v_date.collect()
    dt_min = (
        df_dt.get_column(COL_NAME_DEPARTURE_DATETIME).min() or datetime.now().date()
    )
    dt_max = (
        df_dt.get_column(COL_NAME_DEPARTURE_DATETIME).max() or datetime.now().date()
    )
    dt_min_iso = dt_min.strftime("%Y-%m-%d")
    dt_max_iso = dt_max.strftime("%Y-%m-%d")

    def to_options(lst):
        return [{"label": x, "value": x} for x in lst]

    return (
        to_options(subtypes),
        to_options(matricules),
        dt_min_iso,
        dt_max_iso,
    )


@app.callback(
    Output(FILTER_STORE_SUGGESTIONS, "data"),
    Input(FILTER_SUBTYPE, "value"),
    Input(FILTER_SEGMENTATION, "value"),
    Input(FILTER_MATRICULE, "value"),
    Input(FILTER_DATE_RANGE, "start_date"),
    Input(FILTER_DATE_RANGE, "end_date"),
)
def update_filter_store_suggestions(
    fl_subtype, fl_segmentation, fl_matricule, dt_start, dt_end
):

    print(
        f"Filtering data with: {fl_subtype}, {fl_segmentation}, {fl_matricule}, {dt_start}, {dt_end}"
    )
    if fl_segmentation:
        fl_segmentation = str(fl_segmentation) + UNIT_SEGMENTATION

    return {
        "fl_subtype": fl_subtype,
        "fl_matricule": fl_matricule,
        "fl_segmentation": fl_segmentation,
        "dt_start": dt_start,
        "dt_end": dt_end,
    }


@app.callback(
    Output(ID_DATA_STORE_TRIGGER, "data"),
    add_watch_file(),
    Input(FILTER_STORE_ACTUAL, "data"),
)
def filter_data(_, filter_store_data):

    print("Filtering data with:", filter_store_data)

    df = get_df_unfiltered()

    if df is None:
        return {"payload": [], "count": 0}

    df, total_df = apply_filters(df, filter_store_data)

    update_df(df, total_df)

    return None


@app.callback(
    Output(FILTER_STORE_ACTUAL, "data"),
    Input(FILTER_SUBMIT_BTN, "n_clicks"),
    State(FILTER_STORE_SUGGESTIONS, "data"),
)
def submit_filter(n_clicks, store_suggestions_data):

    return store_suggestions_data


# @app.callback(
#     # 1) Clear the store
#     Output(FILTER_STORE_TRIGGER, "data"),
#     # 2) Reset each control’s value
#     Output(FILTER_SUBTYPE, "value"),
#     Output(FILTER_MATRICULE, "value"),
#     Output(FILTER_SEGMENTATION, "value"),
#     Output(FILTER_DATE_START, "date"),
#     Output(FILTER_DATE_END, "date"),
#     Input(FILTER_RESET_BTN, "n_clicks"),
#     prevent_initial_callbacks=False,
# )
# def reset_all(n_clicks):

#     if not n_clicks:
#         raise dash.exceptions.PreventUpdate

#     cleared = None
#     # --- 2) clear current values ---
#     empty_list = []
#     none_val = None

#     update_df(get_df_unfiltered())

#     return (
#         # 1) store cleared
#         cleared,
#         # 2) values cleared
#         empty_list,
#         empty_list,
#         none_val,
#         none_val,
#         none_val,
#     )
