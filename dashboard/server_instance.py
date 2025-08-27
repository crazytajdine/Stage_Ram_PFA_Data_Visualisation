import dash
import dash_bootstrap_components as dbc
from dash import Dash
import logging

app = None
server = None


def init_server():
    global app, server
    app = Dash(
        __name__,
        suppress_callback_exceptions=True,
        external_stylesheets=[
            "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css",
        ],
    )
    return app, app.server


def get_app() -> dash.Dash:
    global app, server
    if server is None:
        logging.info("Initializing server instance...")
        app, server = init_server()
    return app


def get_server():
    global server, app
    if server is None:
        logging.info("Initializing server instance...")
        app, server = init_server()
    return server
