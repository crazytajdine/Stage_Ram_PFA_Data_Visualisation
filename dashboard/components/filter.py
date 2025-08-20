from typing import Optional
import polars as pl
from dash import Input, Output, State
from utils_dashboard.utils_filter import set_name_from_filter
from data_managers.excel_manager import (
    ID_DATA_STORE_TRIGGER,
    apply_filters,
    update_df,
    get_df_unfiltered,
    add_watch_file,
    get_min_max_date_raw_df,
)
from server_instance import get_app
import dash_bootstrap_components as dbc
from schemas.filter import FilterKey, FilterType

from dash import html, dcc
import logging


FILTER_SUBTYPE = "filter-subtype"
FILTER_MATRICULE = "filter-matricule"
FILTER_SEGMENTATION = "filter-segmentation"
FILTER_SEGMENTATION_UNIT = "filter-segmentation_unit"
FILTER_DATE_RANGE = "filter-date-range"
FILTER_DELAY_CODE = "filter-delay-code"
FILTER_SUBMIT_BTN = "filter-go-btn"
# FILTER_RESET_BTN = "filter-reset-btn"
FILTER_STORE_SUGGESTIONS = "filter-store-suggestions"
FILTER_STORE_ACTUAL = "filter-store-actual"

ID_FILTER_CONTAINER = "filter-container"


app = get_app()

layout = dbc.Card(
    dbc.CardBody(
        [
            dcc.Store(id=FILTER_STORE_SUGGESTIONS),
            dcc.Store(id=FILTER_STORE_ACTUAL),
            html.H4("Filter", className="mb-3"),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Label("Subtype :"),
                            dcc.Dropdown(
                                id=FILTER_SUBTYPE,
                                options=[],
                                multi=True,
                                placeholder="All Options",
                            ),
                        ],
                        md=6,
                    ),
                    dbc.Col(
                        [
                            html.Label("Matricule :"),
                            dcc.Dropdown(
                                id=FILTER_MATRICULE,
                                options=[],
                                multi=True,
                                placeholder="All Options",
                            ),
                        ],
                        md=6,
                    ),
                ],
                className="mb-3",
            ),
            # segmentation
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Label("Segmentation :", htmlFor=FILTER_SEGMENTATION),
                            dbc.InputGroup(
                                [
                                    dbc.Input(
                                        id=FILTER_SEGMENTATION,
                                        placeholder="Select segmentation",
                                        type="number",
                                        min=0,
                                    ),
                                    dbc.Select(
                                        id=FILTER_SEGMENTATION_UNIT,
                                        options=[
                                            {"label": "Day", "value": "d"},
                                            {"label": "Week", "value": "w"},
                                            {"label": "Month", "value": "mo"},
                                            {"label": "Year", "value": "y"},
                                        ],
                                        value="d",
                                    ),
                                ],
                            ),
                        ],
                        md=6,
                    ),
                    dbc.Col(
                        [
                            html.Label("Delay Code :"),
                            dcc.Dropdown(
                                id=FILTER_DELAY_CODE,
                                options=[],
                                multi=True,
                                placeholder="All Options",
                            ),
                        ],
                        md=6,
                    ),
                ],
                className="mb-3",
            ),
            # dates
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Label(
                                "Date :", className="me-2", htmlFor=FILTER_DATE_RANGE
                            ),
                            dcc.DatePickerRange(
                                id=FILTER_DATE_RANGE,
                                clearable=True,
                                display_format="DD-MM-YYYY",
                                number_of_months_shown=2,
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
                            color="primary",  # keeps your RAM red (or Bootstrap blue)
                            className="btn-glass-frame w-100 mb-3",
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
    style={"display": "none"},
    id=ID_FILTER_CONTAINER,
)


def split_views_by_exclusion(
    df: pl.LazyFrame, filters: dict, *excludes: FilterKey
) -> pl.LazyFrame:

    # exclude matricule
    f2 = {**filters, **{exclude: None for exclude in excludes}}
    view_matricule, _ = apply_filters(df, f2, True)

    # exclude both dates
    return view_matricule


def check_segmentation(filter1: FilterType, filter2: FilterType) -> bool:

    unit1 = filter1.get("fl_unit_segmentation")
    unit2 = filter2.get("fl_unit_segmentation")

    segment1 = filter1.get("fl_segmentation", 0)
    segment2 = filter2.get("fl_segmentation", 0)

    if segment1 is None:
        segment1 = 0
    if segment2 is None:
        segment2 = 0

    if segment1 == segment2:

        if segment1 and segment2 and (unit1 != unit2):

            return False

        return True

    return False


def compare_filters(filter1: FilterType, filter2: FilterType):

    is_segments_similar = check_segmentation(filter1, filter2)

    logging.info(f"Comparing filters: {filter1} vs {filter2}")
    filter1 = get_filter_without_segmentation_and_none(filter1)

    filter2 = get_filter_without_segmentation_and_none(filter2)

    logging.info(f"Filtered filters for comparison: {filter1} vs {filter2}")
    return is_segments_similar and (filter1 == filter2)


def get_filter_without_segmentation_and_none(filter: FilterType):
    return (
        {
            k: v
            for k, v in filter.items()
            if v and (k not in ["fl_unit_segmentation", "fl_segmentation"])
        }
        if filter
        else {}
    )


def add_callbacks():

    @app.callback(
        Output(FILTER_SUBTYPE, "options"),
        Output(FILTER_MATRICULE, "options"),
        Output(FILTER_DELAY_CODE, "options"),
        Output(FILTER_DATE_RANGE, "min_date_allowed"),
        Output(FILTER_DATE_RANGE, "max_date_allowed"),
        Input(FILTER_STORE_SUGGESTIONS, "data"),
    )
    def update_filter_options(store_data):

        base_lazy = get_df_unfiltered()  # your global LazyFrame
        if base_lazy is None:
            logging.warning("Base LazyFrame is None, returning empty options.")
            return [], [], [], None, None
        v_sub = split_views_by_exclusion(base_lazy, store_data, "fl_subtypes")
        v_mat = split_views_by_exclusion(base_lazy, store_data, "fl_matricules")
        v_delay = split_views_by_exclusion(base_lazy, store_data, "fl_code_delays")

        # v_date = split_views_by_exclusion(base_lazy, store_data, "dt_start", "dt_end")

        df_delay = v_delay.collect()
        delay_codes = sorted(
            df_delay.get_column("DELAY_CODE").drop_nulls().unique().to_list()
        )

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
        logging.debug("Matricules extracted: %d items", len(matricules))

        # date bounds

        # df_dt = v_date.collect()
        # dt_min = (
        #     df_dt.get_column(COL_NAME_DEPARTURE_DATETIME).min() or datetime.now().date()
        # )
        # dt_max = (
        #     df_dt.get_column(COL_NAME_DEPARTURE_DATETIME).max() or datetime.now().date()
        # )

        dt_min, dt_max = get_min_max_date_raw_df()
        if dt_min or dt_max:
            dt_min_iso = dt_min.strftime("%Y-%m-%d")
            dt_max_iso = dt_max.strftime("%Y-%m-%d")

        def to_options(lst):
            logging.debug(
                "Converting list to dropdown options. List size: %d", len(lst)
            )
            return [{"label": x, "value": x} for x in lst]

        logging.debug(
            "Returning filter dropdown options: subtypes=%d, matricules=%d, delay_codes=%d",
            len(subtypes),
            len(matricules),
            len(delay_codes),
        )

        return (
            to_options(subtypes),
            to_options(matricules),
            to_options(delay_codes),
            dt_min_iso,
            dt_max_iso,
        )

    @app.callback(
        Output(FILTER_SUBMIT_BTN, "color"),
        Input(FILTER_STORE_SUGGESTIONS, "data"),
        Input(FILTER_STORE_ACTUAL, "data"),
        # since i am not putting segmentation and unit into data
        Input(FILTER_SEGMENTATION, "value"),
        Input(FILTER_SEGMENTATION_UNIT, "value"),
    )
    def update_filter_submit_button(
        filter_suggestions, filter_actual, segmentation, segmentation_segmentation_unit
    ):
        logging.debug("Updating filter submit button color")
        logging.debug(
            "Segmentation value: %s | Unit: %s",
            segmentation,
            segmentation_segmentation_unit,
        )

        if filter_suggestions:
            filter_suggestions["fl_segmentation"] = segmentation
            filter_suggestions["fl_unit_segmentation"] = segmentation_segmentation_unit

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
        Input(FILTER_DELAY_CODE, "value"),
        Input(FILTER_DATE_RANGE, "start_date"),
        Input(FILTER_DATE_RANGE, "end_date"),
    )
    def update_filter_store_suggestions(
        fl_subtypes, fl_matricules, fl_code_delays, dt_start, dt_end
    ) -> FilterType:

        logging.info(
            f"Filtering data with: {fl_subtypes}, {fl_matricules}, {fl_code_delays}, {dt_start}, {dt_end}"
        )

        return {
            "fl_subtypes": fl_subtypes,
            "fl_matricules": fl_matricules,
            "fl_code_delays": fl_code_delays,
            "dt_start": dt_start,
            "dt_end": dt_end,
        }

    @app.callback(
        Output(ID_DATA_STORE_TRIGGER, "data"),
        add_watch_file(),
        Input(FILTER_STORE_ACTUAL, "data"),
    )
    def filter_data(_, filter_store_data: FilterType):
        logging.debug(
            "filter_data triggered with filter_store_data: %s", filter_store_data
        )

        df = get_df_unfiltered()

        if df is None:
            logging.warning("Unfiltered DataFrame is None. Returning empty payload.")

            return {"payload": [], "count": 0}
        logging.debug("Applying filters to DataFrame.")
        df, total_df = apply_filters(df, filter_store_data)

        logging.debug("Setting name from filter for display/logging.")
        set_name_from_filter(filter_store_data)

        logging.debug("Updating global DataFrame after filtering.")
        update_df(df, total_df)

        logging.info("Data filtered successfully. Returning payload.")
        return None

    @app.callback(
        Output(FILTER_STORE_ACTUAL, "data"),
        Input(FILTER_SUBMIT_BTN, "n_clicks"),
        State(FILTER_STORE_SUGGESTIONS, "data"),
        # since they will not take effect in the suggestions
        State(FILTER_SEGMENTATION, "value"),
        State(FILTER_SEGMENTATION_UNIT, "value"),
    )
    def submit_filter(
        n_clicks,
        store_suggestions_data: FilterType,
        segmentation: Optional[int],
        segmentation_segmentation_unit: Optional[str],
    ) -> FilterType:
        logging.debug("submit_filter triggered by click %s", n_clicks)
        data = store_suggestions_data if store_suggestions_data else {}
        logging.debug("Initial store_suggestions_data: %s", store_suggestions_data)
        data["fl_segmentation"] = segmentation
        data["fl_unit_segmentation"] = segmentation_segmentation_unit
        logging.info("Filter data submitted: %s", data)
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
