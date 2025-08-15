from dash import Input, Output, State, dcc, html
import dash
import dash_bootstrap_components as dbc

from server_instance import get_app
from services.session_service import delete_session
from data_managers.database_manager import session_scope

ID_AUTH_TOKEN = "token_user_store"
ID_USER_ID = "user_id_store"

app = get_app()


def add_input_user_id():
    return Input(ID_USER_ID, "data")


def add_state_user_id():
    return State(ID_USER_ID, "data")


def add_output_user_id():
    return Output(ID_USER_ID, "data", True)


def add_input_auth_token():
    return Input(ID_AUTH_TOKEN, "data")


def add_output_auth_token():
    return Output(ID_AUTH_TOKEN, "data", True)


logout_button = dbc.Button(
    [html.Span("Logout", className="label")],
    id="logout-btn",
    className="btn-logout",
    color="light",
    outline=True,
)


stores = [dcc.Store(ID_AUTH_TOKEN, "session"), dcc.Store(ID_USER_ID, "session")]


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
