from dash import Dash, html, dcc, Input, Output, State, dash_table
import polars as pl
import dash_bootstrap_components as dbc
from datetime import datetime
import plotly.graph_objs as go

# Fonction pour convertir minutes en "Xh Ym"
def convert_minutes_to_hours_minutes(minutes: int) -> str:
    heures = minutes // 60
    mins = minutes % 60
    return f"{heures}h {mins}m"

# --- Chargement et préparation des données ---
PATH = "tableau.xlsx"
SHEET = "Sheet1"

def create_dep_datetime(path: str, sheet: str) -> pl.DataFrame:
    df = pl.read_excel(path, sheet_name=sheet)
    return df.with_columns([
        (pl.col("DEP_DAY_SCHED").cast(str) + " " + pl.col("DEP_TIME_SCHED").cast(str))
        .str.strptime(pl.Datetime, "%Y-%m-%d %H:%M", strict=False)
        .alias("DEP_DATETIME"),
        (pl.col("AC_SUBTYPE").cast(str) + " - " + pl.col("AC_REGISTRATION").cast(str))
        .alias("AVION_INFO_COMPLETE")
    ])

def filter_tec(df: pl.DataFrame) -> pl.DataFrame:
    return df.filter(pl.col("LIB_CODE_DR") == "TEC")

try:
    df = create_dep_datetime(PATH, SHEET)
    df_tec = filter_tec(df)
except Exception as e:
    print(f"Erreur lors du chargement: {e}")
    df = pl.DataFrame()
    df_tec = pl.DataFrame()

if not df.is_empty():
    dt_min, dt_max = df.get_column("DEP_DATETIME").min(), df.get_column("DEP_DATETIME").max()
else:
    dt_min = dt_max = datetime.now()

dt_min = dt_min or datetime.now()
dt_max = dt_max or datetime.now()
default_dt_iso_start = dt_min.strftime("%Y-%m-%dT%H:%M")
default_dt_iso_end = dt_max.strftime("%Y-%m-%dT%H:%M")

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

custom_css = {
    'container': {'background-color': '#f8f9fa', 'padding': '2rem', 'min-height': '100vh'},
    'header': {'color': '#1a3e72', 'margin-bottom': '2rem', 'font-weight': 'bold'},
    'input': {'border-radius': '4px', 'border': '1px solid #ced4da', 'padding': '0.5rem', 'background-color': 'white'},
    'button': {'border-radius': '4px', 'font-weight': 'bold', 'transition': 'all 0.3s ease'},
    'button:hover': {'transform': 'translateY(-2px)', 'box-shadow': '0 4px 8px rgba(0,0,0,0.1)'},
    'alert': {'border-radius': '4px', 'font-size': '1rem'}
}

app.layout = dbc.Container([
    html.Div(style=custom_css['container'], children=[
        html.H1("Suivi des Vols - Royal Air Maroc", style=custom_css['header'], className="text-center"),
        dbc.Row([
            dbc.Col([
                dbc.Label("Type d'avion", className="fw-bold mb-2"),
                dbc.Input(id='ac-subtype', placeholder='B738...', type='text', style=custom_css['input']),
            ], md=3),
            dbc.Col([
                dbc.Label("Immatriculation", className="fw-bold mb-2"),
                dbc.Input(id='ac-registration', placeholder='CN-ABC...', type='text', style=custom_css['input']),
            ], md=3),
            dbc.Col([
                dbc.Label("Date et heure de départ (début)", className="fw-bold mb-2"),
                dbc.Input(
                    id="dep-datetime-input-start",
                    type="datetime-local",
                    value=default_dt_iso_start,
                    min="1900-01-01T00:00",
                    max="2100-12-31T23:59",
                    style={"width": "100%", 'backgroundColor': custom_css['input']['background-color'], 'color': 'black', 'border': custom_css['input']['border']}
                ),
            ], md=3),
            dbc.Col([
                dbc.Label("Date et heure de départ (fin)", className="fw-bold mb-2"),
                dbc.Input(
                    id="dep-datetime-input-end",
                    type="datetime-local",
                    value=default_dt_iso_end,
                    min="1900-01-01T00:00",
                    max="2100-12-31T23:59",
                    style={"width": "100%", 'backgroundColor': custom_css['input']['background-color'], 'color': 'black', 'border': custom_css['input']['border']}
                ),
            ], md=3),
        ], className="mb-3 g-3"),
        dbc.Alert(id='summary-info', color="info", is_open=False, className="mb-4",
                  style={"fontWeight": "bold", "fontSize": "1.1rem", "whiteSpace": "pre-line"}),
        dbc.Button([html.I(className="fas fa-search me-2"), "Rechercher"], id='search-btn',
                   color="primary", className="w-100 mb-4 py-2", style=custom_css['button']),
        dbc.Alert(id='result-message', is_open=False, dismissable=True, className="mt-3", style=custom_css['alert']),
        dash_table.DataTable(id='result-table', columns=[], data=[], page_size=10,
                             style_table={'overflowX': 'auto'}, style_cell={'textAlign': 'left'}),
        dbc.Row([
            dbc.Col(dcc.Graph(id='bar-chart-pct'), md=6),
            dbc.Col(dcc.Graph(id='bar-chart-mean'), md=6)
        ], className="mt-4")
    ])
], fluid=True)


@app.callback(
    [Output('summary-info', 'children'),
     Output('summary-info', 'is_open'),
     Output('result-message', 'children'),
     Output('result-message', 'color'),
     Output('result-message', 'is_open'),
     Output('result-table', 'columns'),
     Output('result-table', 'data'),
     Output('bar-chart-pct', 'figure'),
     Output('bar-chart-mean', 'figure')],
    Input('search-btn', 'n_clicks'),
    [State('ac-subtype', 'value'),
     State('ac-registration', 'value'),
     State('dep-datetime-input-start', 'value'),
     State('dep-datetime-input-end', 'value')]
)
def search_flight(n_clicks, ac_type, ac_reg, dt_start_str, dt_end_str):
    if not n_clicks:
        return "", False, "", "primary", False, [], [], {}, {}

    try:
        ac_type = ac_type.strip().lower() if ac_type else None
        ac_reg = ac_reg.strip().lower() if ac_reg else None

        dt_start = datetime.strptime(dt_start_str, "%Y-%m-%dT%H:%M") if dt_start_str else None
        dt_end = datetime.strptime(dt_end_str, "%Y-%m-%dT%H:%M") if dt_end_str else None

        df_filtered = df

        if ac_type:
            df_filtered = df_filtered.filter(pl.col("AC_SUBTYPE").str.to_lowercase() == ac_type)
        if ac_reg:
            df_filtered = df_filtered.filter(pl.col("AC_REGISTRATION").str.to_lowercase() == ac_reg)

        # Filtrage par intervalle date/heure
        if dt_start and dt_end:
            df_filtered = df_filtered.filter(
                (pl.col("DEP_DATETIME") >= dt_start) & (pl.col("DEP_DATETIME") <= dt_end)
            )
        elif dt_start:
            df_filtered = df_filtered.filter(pl.col("DEP_DATETIME") >= dt_start)
        elif dt_end:
            df_filtered = df_filtered.filter(pl.col("DEP_DATETIME") <= dt_end)

        # Définition de cols avant utilisation
        cols = ["AC_SUBTYPE", "AC_REGISTRATION", "DEP_DATETIME", "Retard en min", "CODE_DR"]

        df_filtered = df_filtered.filter(pl.col("Retard en min") != 0)

        if df_filtered.is_empty():
            return (
                "", False,
                dbc.Alert("Aucun résultat trouvé pour les critères spécifiés.", color="warning", className="mt-3"),
                "warning", True, [], [], {}, {}
            )

        nb_retard_15 = df_filtered.filter(pl.col("Retard en min") >= 15).height

        df_max_retard = df_filtered.filter(pl.col("Retard en min") > 0).sort("Retard en min", descending=True).limit(1)
        if df_max_retard.height > 0:
            vol_max = df_max_retard[0]
            subtype = vol_max['AC_SUBTYPE']
            if hasattr(subtype, 'item'):
                subtype = subtype.item()
            registration = vol_max['AC_REGISTRATION']
            if hasattr(registration, 'item'):
                registration = registration.item()
            retard_min = vol_max['Retard en min']
            if hasattr(retard_min, 'item'):
                retard_min = retard_min.item()
            retard_hm = convert_minutes_to_hours_minutes(retard_min)
            somme_retards = df_filtered.select(pl.col("Retard en min").sum()).to_dicts()[0].get("Retard en min", 0)
            somme_retards_hm = convert_minutes_to_hours_minutes(somme_retards)
            vol_info = (
                f"\nVol avec le plus grand retard est {subtype} {registration}, "
                f"durée du retard : {retard_hm} ({retard_min} min)\n"
                f"somme des retards en min : {somme_retards} min ({somme_retards_hm})"
            )
        else:
            vol_info = "\nAucun vol avec retard supérieur à 0 min."

        summary_text = f"Nombre de vols avec retard ≥ 15 min : {nb_retard_15}{vol_info}"

        if "DEP_DATETIME" in df_filtered.columns:
            df_filtered = df_filtered.with_columns(
                pl.col("DEP_DATETIME").dt.strftime("%Y-%m-%d %H:%M").alias("DEP_DATETIME")
            )

        df_display = df_filtered.select(cols).rename({
            "AC_SUBTYPE": "SUBTYPE",
            "AC_REGISTRATION": "REGISTRATION",
            "DEP_DATETIME": "DATETIME",
            "CODE_DR": "CODE RETARD",
            "Retard en min": "RETARD (min)"
        })

        columns = [{"name": col, "id": col} for col in df_display.columns]
        data = df_display.to_dicts()

        total = df_filtered.height
        count_15_plus = df_filtered.filter(pl.col("Retard en min") >= 15).height if total > 0 else 0
        count_15_moins = df_filtered.filter(pl.col("Retard en min") < 15).height if total > 0 else 0
        pct_15_plus = (count_15_plus / total) * 100 if total > 0 else 0
        pct_15_moins = (count_15_moins / total) * 100 if total > 0 else 0

        mean_15_plus = df_filtered.filter(pl.col("Retard en min") >= 15).select(pl.col("Retard en min").mean()).to_dicts()[0].get("Retard en min", 0) if count_15_plus > 0 else 0
        mean_15_moins = df_filtered.filter(pl.col("Retard en min") < 15).select(pl.col("Retard en min").mean()).to_dicts()[0].get("Retard en min", 0) if count_15_moins > 0 else 0

        fig_pct = go.Figure(data=[
            go.Bar(
                x=["Retard < 15 min", "Retard ≥ 15 min"],
                y=[pct_15_moins, pct_15_plus],
                marker_color=['#1a3e72', '#1a3e72']
            )
        ])
        fig_pct.update_layout(
            title="Pourcentage des vols par catégorie de retard",
            yaxis_title="Pourcentage (%)",
            xaxis_title="Catégorie",
            yaxis=dict(range=[0, 100])
        )

        fig_mean = go.Figure(data=[
            go.Bar(
                x=["Retard < 15 min", "Retard ≥ 15 min"],
                y=[mean_15_moins, mean_15_plus],
                marker_color=['#1a3e72', '#1a3e72']
            )
        ])
        fig_mean.update_layout(
            title="Moyenne du retard par catégorie",
            yaxis_title="Durée moyenne (minutes)",
            xaxis_title="Catégorie"
        )

        return (
            summary_text,
            True,
            dbc.Alert(f"{len(data)} résultat(s) trouvé(s).", color="success", className="mt-3"),
            "success",
            True,
            columns,
            data,
            fig_pct,
            fig_mean
        )
    except Exception as e:
        return (
            "",
            False,
            dbc.Alert(f"Erreur technique: {str(e)}", color="danger", className="mt-3"),
            "danger",
            True,
            [],
            [],
            {},
            {}
        )


if __name__ == '__main__':
    app.run(debug=True)
