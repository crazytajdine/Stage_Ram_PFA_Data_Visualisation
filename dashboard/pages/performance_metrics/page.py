from server_instance import get_app
from excel_manager import update_path_to_excel
import dash_bootstrap_components as dbc

from dash import html, dcc


app = get_app()

layout = html.Div("Performance Metrics Page")
