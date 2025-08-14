from dash import Input, Output, State, dcc, html
import dash
import dash_bootstrap_components as dbc

from server_instance import get_app
from services.session_service import delete_session
from data_managers.database_manager import session_scope

ID_AUTH_TOKEN = "token_user"

app = get_app()


def add_input_auth_token():
    return Input(ID_AUTH_TOKEN, "data", True)


def add_output_auth_token():
    return Output(ID_AUTH_TOKEN, "data", True)


logout_button = dbc.Button(
    [html.Span("Logout", className="label")],
    id="logout-btn",
    className="btn-logout",
    color="light",
    outline=True,
)


stores = [dcc.Store(ID_AUTH_TOKEN, "session")]


def add_callbacks():
    @app.callback(
        Output(ID_AUTH_TOKEN, "data"),
        Input("logout-btn", "n_clicks", True),
        State(ID_AUTH_TOKEN, "data"),
        prevent_initial_call=True,
    )
    def handle_logout(n_clicks, token):
        if not n_clicks:
            raise dash.exceptions.PreventUpdate

        with session_scope() as session:
            delete_session(token, session)

        return None
