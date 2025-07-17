from dash import html, dcc, Input, Output, State, dash_table, callback_context
import polars as pl
import dash_bootstrap_components as dbc
from datetime import datetime, timedelta
import plotly.graph_objs as go
import math

from excel_manager import get_df
from server_instance import get_app

app = get_app()

custom_css = {
    "container": {"background-color": "#f8f9fa", "padding": "2rem", "min-height": "100vh"},
    "header": {"color": "#1a3e72", "margin-bottom": "2rem", "font-weight": "bold"},
    "input": {"border-radius": "4px", "border": "1px solid #ced4da", "padding": "0.5rem", "background-color": "white"},
    "button": {"border-radius": "4px", "font-weight": "bold", "transition": "all 0.3s ease"},
    "button:hover": {"transform": "translateY(-2px)", "box-shadow": "0 4px 8px rgba(0,0,0,0.1)"},
    "alert": {"border-radius": "4px", "font-size": "1rem"},
}

def convert_minutes_to_hours_minutes(minutes: int) -> str:
    heures = minutes // 60
    mins = minutes % 60
    return f"{heures}h {mins}m"

layout = dbc.Container(
    [
        html.Div(
            style=custom_css["container"],
            children=[
                html.H1("Suivi des Vols - Royal Air Maroc", style=custom_css["header"], className="text-center"),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Type d'avion", className="fw-bold mb-2"),
                        dcc.Dropdown(id="ac-subtype", options=[], multi=True, placeholder="Tous les types", style={"background-color": "white"}),
                    ], md=3),
                    dbc.Col([
                        dbc.Label("Immatriculation", className="fw-bold mb-2"),
                        dcc.Dropdown(id="ac-registration", options=[], multi=True, placeholder="Toutes les immatriculations", style={"background-color": "white"}),
                    ], md=3),
                    dbc.Col([
                        dbc.Label("Date et heure de départ (début)", className="fw-bold mb-2"),
                        dbc.Input(id="dep-datetime-input-start", type="datetime-local", min="1900-01-01T00:00", max="2100-12-31T23:59",
                                  style={"width": "100%", "backgroundColor": custom_css["input"]["background-color"], "color": "black", "border": custom_css["input"]["border"]}),
                    ], md=3),
                    dbc.Col([
                        dbc.Label("Date et heure d'arrivée (fin)", className="fw-bold mb-2"),
                        dbc.Input(id="dep-datetime-input-end", type="datetime-local", min="1900-01-01T00:00", max="2100-12-31T23:59",
                                  style={"width": "100%", "backgroundColor": custom_css["input"]["background-color"], "color": "black", "border": custom_css["input"]["border"]}),
                    ], md=3),
                ], className="mb-3 g-3"),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Code de retard", className="fw-bold mb-2"),
                        dcc.Dropdown(id="code-dr", options=[], multi=True, placeholder="Tous les codes", style={"background-color": "white"}),
                    ], md=12),
                ], className="mb-3"),
                dbc.Alert(id="summary-info", color="info", is_open=False, className="mb-4",
                          style={"fontWeight": "bold", "fontSize": "1.1rem", "whiteSpace": "pre-line"}),
                dbc.Button([html.I(className="fas fa-search me-2"), "Rechercher"], id="search-btn", color="primary",
                           className="w-100 mb-4 py-2", style=custom_css["button"]),
                dbc.Row([
                    dbc.Col(dcc.Graph(id="bar-chart-pct"), md=6),
                    dbc.Col(dcc.Graph(id="bar-chart-interval", style={'width': '100%', 'height': '700px'}), md=6),
                ], className="mt-4 mb-2"),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Taille de l’intervalle en jours pour regroupement", className="fw-bold mt-3"),
                        dbc.Input(id="interval-days-input", type="number", min=1, step=1, value=1, style={"maxWidth": "150px"}, debounce=True),
                    ], md=3),
                    dbc.Col(
                        dbc.Button("Confirmer l'intervalle", id="confirm-interval-btn", color="secondary", className="mt-4", style={"maxWidth": "150px"}),
                        md=1,
                    ),
                ]),
                dbc.Alert(id="result-message", is_open=False, dismissable=True, className="mt-3", style=custom_css["alert"]),
                dash_table.DataTable(id="result-table", columns=[], data=[], page_size=10,
                                     style_table={"overflowX": "auto"}, style_cell={"textAlign": "left"}, sort_action='native'),
            ]
        )
    ],
    fluid=True,
)

# ---------------------------------------------
# AJOUT POUR REMPLISSAGE DYNAMIQUE DES DROPDOWNS
# ---------------------------------------------
@app.callback(
    Output("ac-subtype", "options"),
    Output("ac-registration", "options"),
    Output("code-dr", "options"),
    Input("search-btn", "n_clicks"),
)
def populate_dropdown_options(n):
    df = get_df()
    if df is not None:
        df = df.collect()
        opts_subtype = [{"label": v, "value": v} for v in sorted(df.get_column("AC_SUBTYPE").unique().to_list()) if v] if "AC_SUBTYPE" in df.columns else []
        opts_reg    = [{"label": v, "value": v} for v in sorted(df.get_column("AC_REGISTRATION").unique().to_list()) if v] if "AC_REGISTRATION" in df.columns else []
        opts_code   = [{"label": v, "value": v} for v in sorted(df.get_column("CODE_DR").unique().to_list()) if v] if "CODE_DR" in df.columns else []
        return opts_subtype, opts_reg, opts_code
    else:
        return [], [], []
# ------------------------------------------------

@app.callback(
    [
        Output("summary-info", "children"),
        Output("summary-info", "is_open"),
        Output("result-message", "children"),
        Output("result-message", "color"),
        Output("result-message", "is_open"),
        Output("result-table", "columns"),
        Output("result-table", "data"),
        Output("bar-chart-pct", "figure"),
        Output("bar-chart-interval", "figure"),
    ],
    [
        Input("search-btn", "n_clicks"),
        Input("confirm-interval-btn", "n_clicks"),
    ],
    [
        State("ac-subtype", "value"),
        State("ac-registration", "value"),
        State("code-dr", "value"),
        State("dep-datetime-input-start", "value"),
        State("dep-datetime-input-end", "value"),
        State("interval-days-input", "value"),
    ],
)
def update_outputs(search_clicks, confirm_clicks, ac_types, ac_regs, codes_dr_vals, dt_start_str, dt_end_str, interval_days):
    ctx = callback_context
    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0] if ctx.triggered else None

    empty_fig = go.Figure()
    empty_columns = []
    empty_data = []

    df = get_df()
    if df is None:
        error_alert = dbc.Alert("Aucun fichier Excel chargé. Veuillez charger un fichier Excel d'abord.", color="danger", className="mt-3")
        if triggered_id == "search-btn":
            return "", False, error_alert, "danger", True, empty_columns, empty_data, empty_fig, empty_fig
        else:
            return (dash.no_update,) * 9

    df = df.collect()
    try:
        if ac_types:
            vals_lower = [v.lower() for v in ac_types]
            df = df.filter(pl.col("AC_SUBTYPE").str.to_lowercase().is_in(vals_lower))
        if ac_regs:
            vals_lower = [v.lower() for v in ac_regs]
            df = df.filter(pl.col("AC_REGISTRATION").str.to_lowercase().is_in(vals_lower))
        if codes_dr_vals:
            df = df.filter(pl.col("CODE_DR").is_in(codes_dr_vals))

        dt_start = None
        dt_end = None
        if dt_start_str:
            try:
                dt_start = datetime.strptime(dt_start_str, "%Y-%m-%dT%H:%M")
            except:
                dt_start = None
        if dt_end_str:
            try:
                dt_end = datetime.strptime(dt_end_str, "%Y-%m-%dT%H:%M")
            except:
                dt_end = None

        if dt_start and dt_end:
            df = df.filter((pl.col("DEP_DAY_SCHED") >= dt_start) & (pl.col("DEP_DAY_SCHED") <= dt_end))
        elif dt_start:
            df = df.filter(pl.col("DEP_DAY_SCHED") >= dt_start)
        elif dt_end:
            df = df.filter(pl.col("DEP_DAY_SCHED") <= dt_end)

        if df.is_empty():
            warning_alert = dbc.Alert("Aucun résultat trouvé pour les critères spécifiés.", color="warning", className="mt-3")
            if triggered_id == "search-btn":
                return "", False, warning_alert, "warning", True, empty_columns, empty_data, empty_fig, empty_fig
            else:
                return (dash.no_update,) * 9

        df = df.sort("Retard en min", descending=True)

        if triggered_id == "search-btn":
            nb_retard_15 = df.filter(pl.col("Retard en min") >= 15).height
            df_max_retard = df.filter(pl.col("Retard en min") > 0).limit(1)
            if df_max_retard.height > 0:
                vol_max = df_max_retard[0]
                subtype = vol_max["AC_SUBTYPE"]
                subtype = subtype.item() if hasattr(subtype, "item") else subtype
                registration = vol_max["AC_REGISTRATION"]
                registration = registration.item() if hasattr(registration, "item") else registration
                retard_min = vol_max["Retard en min"]
                retard_min = retard_min.item() if hasattr(retard_min, "item") else retard_min
                retard_hm = convert_minutes_to_hours_minutes(retard_min)
                vol_info = f"\nVol avec le plus grand retard est {subtype} {registration}, durée du retard : {retard_hm} ({retard_min} min)\n"
            else:
                vol_info = "\nAucun vol avec retard supérieur à 0 min."

            summary_text = f"Nombre de vols avec retard ≥ 15 min : {nb_retard_15}{vol_info}"

            df_display = df.select(
                ["AC_SUBTYPE", "AC_REGISTRATION", "DEP_DAY_SCHED", "Retard en min", "CODE_DR"]
            ).rename(
                {
                    "AC_SUBTYPE": "SUBTYPE",
                    "AC_REGISTRATION": "REGISTRATION",
                    "DEP_DAY_SCHED": "DATETIME",
                    "CODE_DR": "CODE RETARD",
                    "Retard en min": "RETARD (min)",
                }
            )

            columns = [{"name": col, "id": col} for col in df_display.columns]
            data = df_display.to_dicts()

            total = df.height
            count_15_plus = df.filter(pl.col("Retard en min") >= 15).height if total > 0 else 0
            count_15_moins = df.filter(pl.col("Retard en min") < 15).height if total > 0 else 0
            pct_15_plus = (count_15_plus / total) * 100 if total > 0 else 0
            pct_15_moins = (count_15_moins / total) * 100 if total > 0 else 0

            fig_pct = go.Figure(
                data=[
                    go.Bar(
                        x=["Retard < 15 min", "Retard ≥ 15 min"],
                        y=[pct_15_moins, pct_15_plus],
                    )
                ]
            )
            fig_pct.update_layout(
                title="Pourcentage des vols par catégorie de retard",
                yaxis_title="Pourcentage (%)",
                xaxis_title="Catégorie",
                yaxis=dict(range=[0, 100]),
            )

            fig_interval = build_interval_figure(df, interval_days)

            return (
                summary_text,
                True,
                dbc.Alert(f"{len(data)} résultat(s) trouvé(s).", color="success", className="mt-3"),
                "success",
                True,
                columns,
                data,
                fig_pct,
                fig_interval,
            )

        elif triggered_id == "confirm-interval-btn":
            fig_interval = build_interval_figure(df, interval_days)
            return (dash.no_update,) * 8 + (fig_interval,)

        else:
            return (dash.no_update,) * 9

    except Exception as e:
        print(f"Exception dans le callback combiné: {e}")
        return (
            "",
            False,
            dbc.Alert(f"Erreur technique: {str(e)}", color="danger", className="mt-3"),
            "danger",
            True,
            [],
            [],
            go.Figure(),
            go.Figure(),
        )

def build_interval_figure(df, interval_days):
    if not interval_days or interval_days <= 0:
        interval_days = 1

    dt_col = df.get_column("DEP_DAY_SCHED")
    dt_min = dt_col.min()
    dt_max = dt_col.max()

    total_days = (dt_max - dt_min).days + 1
    n_intervals = math.ceil(total_days / interval_days)

    intervals = []
    labels = []
    for i in range(n_intervals):
        start_int = dt_min + timedelta(days=i * interval_days)
        end_int = min(start_int + timedelta(days=interval_days - 1, hours=23, minutes=59, seconds=59), dt_max)
        intervals.append((start_int, end_int))
        labels.append(f"{start_int.strftime('%Y-%m-%d')} → {end_int.strftime('%Y-%m-%d')}")

    counts = []
    for start_i, end_i in intervals:
        count = df.filter(
            (pl.col("DEP_DAY_SCHED") >= start_i) & (pl.col("DEP_DAY_SCHED") <= end_i)
        ).height
        counts.append(count)

    total_vols = sum(counts) if counts else 1
    percents = [100 * cnt / total_vols if total_vols > 0 else 0 for cnt in counts]

    fig_interval = go.Figure(
        data=[
            go.Bar(
                x=labels,
                y=percents,
                text=[f"{cnt} vols" for cnt in counts],
                textposition='auto',
            )
        ]
    )
    fig_interval.update_layout(
        title=f"Répartition des vols par intervalles de {interval_days} jour(s)",
        yaxis_title="Pourcentage (%)",
        xaxis_title="Intervalle de dates",
        yaxis=dict(range=[0, 100]),
        xaxis_tickangle=-45,
        margin=dict(b=150),
        width=1000,
        height=600
    )

    return fig_interval

app.layout = layout
