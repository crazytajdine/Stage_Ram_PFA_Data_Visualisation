import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import pandas as pd
import numpy as np
import requests

# Sample data
df = pd.DataFrame({
    "Date": pd.date_range(start="2024-01-01", periods=100),
    "Sales": (1000 + np.random.randn(100).cumsum()).astype(int),
    "Region": ["North", "South", "East", "West"] *25,
    "Reg": ["N", "S", "E", "W"] *25
})

# Initialize Dash app
app = dash.Dash(__name__)
app.title = "Simple Sales Dashboard"

# Layout
app.layout = html.Div([
    html.H1("Sales Dashboard", style={'textAlign': 'center'}),

    html.Label("Select Region:"),
    dcc.Dropdown(
        id="region-dropdown",
        options=[{"label": region, "value": region} for region in df["Region"].unique()],
        value="North"
    ),


    dcc.Graph(id="sales-graph"),

    html.Div(id="stats-output", style={"marginTop": 20}),
])

# Callbacks
@app.callback(
    Output("sales-graph", "figure"),
    Output("stats-output", "children"),
    Input("region-dropdown", "value"),
)
def update_graph(region):
    print(region)
    if(region):
        filtered_df = df[df["Region"] == region]
    else:
        filtered_df = df
    fig = px.line(filtered_df, x="Date", y="Sales", title=f"Sales Over Time - {region}")
    stats = f"Average Sales: {filtered_df['Sales'].mean():.2f} | Max: {filtered_df['Sales'].max()} | Min: {filtered_df['Sales'].min()}"
    return fig, stats

# Run the app
if __name__ == '__main__':
    try:
        app.run(debug=True)
    except OSError as e:
        if e.errno == 98:  
            print("Port is already in use. Exiting...")
        else:
            raise
