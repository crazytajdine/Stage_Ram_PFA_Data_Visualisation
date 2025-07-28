from typing import Optional, Tuple
import dash
import polars as pl
from datetime import date, datetime
from dash import Input, Output, State
from excel_manager import (
    COL_NAME_DEPARTURE_DATETIME,
    COL_NAME_WINDOW_TIME,
    COL_NAME_WINDOW_TIME_MAX,
    ID_DATA_STORE_TRIGGER,
    update_df,
    get_df_unfiltered,
    add_watch_file,
    get_count_df,
    get_min_max_date_raw_df,
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

ID_FILTER_CONTAINER = "filter-container"

ID_FILTER_TITLE = "filter_title"

app = get_app()


layout = dbc.Card(
    dbc.CardBody(
        [
            dcc.Store(id=FILTER_STORE_SUGGESTIONS),
            dcc.Store(id=FILTER_STORE_ACTUAL),
            html.H2("Title", id=ID_FILTER_TITLE),
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
                                display_format="DD-MM-YYYY",
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
                            type="submit",
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
    id=ID_FILTER_CONTAINER,
)


def apply_filters(
    df: pl.LazyFrame, filters: Optional[dict], is_suggestions=False
) -> Tuple[pl.LazyFrame, Optional[pl.LazyFrame]]:
    total_df = None

    segmentation = filters.get("fl_segmentation") if filters else None
    unit_segmentation = filters.get("fl_unit_segmentation") if filters else None
    subtypes = filters.get("fl_subtype") if filters else None
    matricules = filters.get("fl_matricule") if filters else None
    min_dt = filters.get("dt_start") if filters else None
    max_dt = filters.get("dt_end") if filters else None

    start = end = None
    if (not segmentation) and (not min_dt or not max_dt):
        min_total_dt, max_total_dt = get_min_max_date_raw_df()

    if min_dt:
        start = (
            min_dt
            if isinstance(min_dt, date)
            else datetime.fromisoformat(min_dt).date()
        )
        stmt_start = pl.lit(start)
    else:
        if segmentation:
            stmt_start = pl.lit(COL_NAME_DEPARTURE_DATETIME).min()
        else:
            stmt_start = pl.lit(min_total_dt)

    if max_dt:
        end = (
            max_dt
            if isinstance(max_dt, date)
            else datetime.fromisoformat(max_dt).date()
        )
        stmt_end = pl.lit(end)
    else:
        if segmentation:
            stmt_end = pl.col(COL_NAME_DEPARTURE_DATETIME).max()
        else:
            stmt_end = pl.lit(max_total_dt)

    if not is_suggestions:
        total_df = get_count_df(segmentation, unit_segmentation, start, end)

    stmt_start = stmt_start.alias(COL_NAME_WINDOW_TIME)
    stmt_end = stmt_end.alias(COL_NAME_WINDOW_TIME_MAX)

    if not filters:

        df = df.with_columns(
            stmt_start,
            stmt_end,
        )

        return df, total_df

    # Filter by AC_SUBTYPE
    if subtypes:
        df = df.filter(pl.col("AC_SUBTYPE").is_in(subtypes))

    # Filter by AC_REGISTRATION
    if matricules:
        df = df.filter(pl.col("AC_REGISTRATION").is_in(matricules))

    # Filter by SEGMENTATION
    if segmentation:
        min_segmentation = str(segmentation) + unit_segmentation
        max_segmentation = str(segmentation - 1) + unit_segmentation

        df = df.with_columns(
            pl.col(COL_NAME_DEPARTURE_DATETIME)
            .dt.truncate(min_segmentation)
            .alias(COL_NAME_WINDOW_TIME)
        ).with_columns(
            pl.col(COL_NAME_WINDOW_TIME)
            .dt.offset_by(max_segmentation)
            .alias(COL_NAME_WINDOW_TIME_MAX),
        )

    else:

        df = df.with_columns(
            stmt_start,
            stmt_end,
        )

    # Filter by date range (DEP_DAY_SCHED)
    if start:

        df = df.filter(pl.col(COL_NAME_DEPARTURE_DATETIME) >= start)

    if end:

        df = df.filter(pl.col(COL_NAME_DEPARTURE_DATETIME) <= end)

    return df, total_df


def split_views_by_exclusion(
    df: pl.LazyFrame, filters: dict, *excludes: str
) -> pl.LazyFrame:

    # exclude matricule
    f2 = {**filters, **{exclude: None for exclude in excludes}}
    view_matricule, _ = apply_filters(df, f2, True)

    # exclude both dates
    return view_matricule


def compare_filters(filter1: Optional[dict], filter2: Optional[dict]):

    filter1 = {k: v for k, v in filter1.items() if v is not None} if filter1 else {}

    filter2 = {k: v for k, v in filter2.items() if v is not None} if filter2 else {}

    return filter1 == filter2


def add_callbacks():

    @app.callback(
        Output(FILTER_SUBTYPE, "options"),
        Output(FILTER_MATRICULE, "options"),
        Output(FILTER_DATE_RANGE, "min_date_allowed"),
        Output(FILTER_DATE_RANGE, "max_date_allowed"),
        Input(FILTER_STORE_SUGGESTIONS, "data"),
    )
    def update_filter_options(store_data):

        base_lazy = get_df_unfiltered()  # your global LazyFrame

        v_sub = split_views_by_exclusion(base_lazy, store_data, "fl_subtype")
        v_mat = split_views_by_exclusion(base_lazy, store_data, "fl_matricule")
        # v_date = split_views_by_exclusion(base_lazy, store_data, "dt_start", "dt_end")

        # subtype dropdown
        df_sub = v_sub.collect()
        subtypes = sorted(
            df_sub.get_column("AC_SUBTYPE").drop_nulls().unique().to_list()
        )

        # matricule dropdown
        df_mat = v_mat.collect()
        matricules = sorted(
            df_mat.get_column("AC_REGISTRATION").drop_nulls().unique().to_list()
        )

        # date bounds

        # df_dt = v_date.collect()
        # dt_min = (
        #     df_dt.get_column(COL_NAME_DEPARTURE_DATETIME).min() or datetime.now().date()
        # )
        # dt_max = (
        #     df_dt.get_column(COL_NAME_DEPARTURE_DATETIME).max() or datetime.now().date()
        # )

        dt_min, dt_max = get_min_max_date_raw_df()

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
        Output(FILTER_SUBMIT_BTN, "color"),
        Input(FILTER_STORE_SUGGESTIONS, "data"),
        Input(FILTER_STORE_ACTUAL, "data"),
        # since i am not putting segmentation and unit into data
        Input(FILTER_SEGMENTATION, "value"),
    )
    def update_filter_submit_button(filter_suggestions, filter_actual, segmentation):

        if filter_suggestions:
            filter_suggestions["fl_segmentation"] = segmentation
            filter_suggestions["fl_unit_segmentation"] = "d"

        color = (
            "primary"
            if compare_filters(filter_suggestions, filter_actual)
            else "warning"
        )

        return color

    @app.callback(
        Output(FILTER_STORE_SUGGESTIONS, "data"),
        Input(FILTER_SUBTYPE, "value"),
        Input(FILTER_MATRICULE, "value"),
        Input(FILTER_DATE_RANGE, "start_date"),
        Input(FILTER_DATE_RANGE, "end_date"),
    )
    def update_filter_store_suggestions(fl_subtype, fl_matricule, dt_start, dt_end):

        print(
            f"Filtering data with: {fl_subtype}, {fl_matricule}, {dt_start}, {dt_end}"
        )

        return {
            "fl_subtype": fl_subtype,
            "fl_matricule": fl_matricule,
            "dt_start": dt_start,
            "dt_end": dt_end,
        }

    @app.callback(
        Output(ID_DATA_STORE_TRIGGER, "data"),
        add_watch_file(),
        Input(FILTER_STORE_ACTUAL, "data"),
    )
    def filter_data(_, filter_store_data):

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
        # since they will not take effect in the suggestions
        State(FILTER_SEGMENTATION, "value"),
    )
    def submit_filter(
        n_clicks, store_suggestions_data: Optional[dict], segmentation: Optional[int]
    ):
        data = store_suggestions_data if store_suggestions_data else {}
        data["fl_segmentation"] = segmentation
        data["fl_unit_segmentation"] = "d"
        return data


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
