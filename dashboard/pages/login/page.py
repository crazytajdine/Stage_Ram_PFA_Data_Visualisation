# dashboard/pages/login/page.py
from dash import html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
import dash
from datetime import datetime

from server_instance import get_app
from data_managers.auth_db_manager import AuthDatabaseManager
from data_managers.session_manager import SessionManager

# use nav metadata to determine the FIRST visible tab to land on
from configurations.nav_config import build_nav_items_meta
from data_managers.excel_manager import path_exists

app = get_app()
auth_db = AuthDatabaseManager()
session_manager = SessionManager()

# top:
from data_managers.auth_db_manager import AuthDatabaseManager
from configurations.nav_config import build_nav_items_meta
from data_managers.excel_manager import path_exists
AUTH_DB = AuthDatabaseManager()

def _slug(href: str | None) -> str:
    return (href or "/").lstrip("/").rstrip("/").lower()

def _first_allowed_href(does_path_exists: bool, role: str | None) -> str:
    meta = build_nav_items_meta(does_path_exists) or []
    allowed = None if role == "admin" else set(AUTH_DB.get_allowed_pages_for_role(role) or [])
    visible = [
        m for m in meta
        if getattr(m, "show", True)
        and (_slug(m.href) != "admin" or role == "admin")
        and (allowed is None or _slug(m.href) in allowed)
    ]
    if not visible:
        return "/dashboard"
    dash_item = next((m for m in visible if (m.name or "").strip().lower() == "dashboard" or _slug(m.href) == "dashboard"), None)
    return (dash_item or visible[0]).href


layout = html.Div(
    [
        # Background with gradient
        html.Div(
            style={
                "position": "fixed",
                "top": 0, "left": 0, "right": 0, "bottom": 0,
                "background": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                "zIndex": -1,
            }
        ),

        dbc.Container(
            dbc.Row(
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.Div(
                                    [
                                        html.Img(
                                            src=app.get_asset_url("logo_ram-2.png"),
                                            style={"height": "120px", "display": "block", "margin": "0 auto 20px"},
                                        ),
                                        html.H3("Delay Dashboard", className="text-center mb-0"),
                                        html.P("Royal Air Maroc", className="text-center text-muted mb-4"),
                                    ]
                                ),
                                html.Hr(),

                                # Login Form
                                dbc.Form(
                                    [
                                        dbc.Row(
                                            dbc.Col(
                                                html.Div(
                                                    [
                                                        dbc.Label(
                                                            [html.I(className="bi bi-envelope me-2"), "Email Address"],
                                                            html_for="login-email",
                                                        ),
                                                        dbc.Input(
                                                            id="login-email",
                                                            type="email",
                                                            placeholder="user@royalair.ma",
                                                            className="form-control-lg",
                                                            autoFocus=True,
                                                        ),
                                                        dbc.FormText("Must be a valid email address"),
                                                    ],
                                                    className="mb-3",
                                                )
                                            )
                                        ),
                                        dbc.Row(
                                            dbc.Col(
                                                html.Div(
                                                    [
                                                        dbc.Label(
                                                            [html.I(className="bi bi-lock me-2"), "Password"],
                                                            html_for="login-password",
                                                        ),
                                                        dbc.Input(
                                                            id="login-password",
                                                            type="password",
                                                            placeholder="Enter your password",
                                                            className="form-control-lg",
                                                        ),
                                                        dbc.FormText("Minimum 8 characters"),
                                                    ],
                                                    className="mb-4",
                                                )
                                            )
                                        ),
                                        dbc.Row(
                                            dbc.Col(
                                                dbc.Button(
                                                    [html.I(className="bi bi-box-arrow-in-right me-2"), "Sign In"],
                                                    id="login-button",
                                                    color="primary",
                                                    className="w-100 btn-lg",
                                                    n_clicks=0,
                                                )
                                            )
                                        ),
                                    ],
                                    id="login-form",
                                ),

                                # Alert for errors
                                dbc.Alert(id="login-alert", is_open=False, dismissable=True, className="mt-3"),

                                # Footer info
                                html.Div(
                                    [
                                        html.Hr(className="mt-4"),
                                        html.P(
                                            [html.I(className="bi bi-info-circle me-2"), "Contact your administrator for access"],
                                            className="text-center text-muted small mb-0",
                                        ),
                                    ]
                                ),
                            ]
                        ),
                        className="shadow-lg",
                        style={"maxWidth": "450px", "borderRadius": "15px", "border": "none"},
                    ),
                    width=12,
                    lg=5,
                    className="mx-auto",
                ),
                className="vh-100 d-flex align-items-center",
            ),
            fluid=True,
        ),

        # Loading overlay
        dcc.Loading(id="login-loading", type="circle", children=html.Div(id="login-loading-output")),
    ]
)


@app.callback(
    [
        Output("session-store", "data"),
        Output("login-alert", "children"),
        Output("login-alert", "color"),
        Output("login-alert", "is_open"),
        Output("url", "pathname", allow_duplicate=True),   # <-- IMPORTANT
        Output("login-loading-output", "children"),
    ],
    [Input("login-button", "n_clicks"), Input("login-password", "n_submit")],
    [State("login-email", "value"), State("login-password", "value")],
    prevent_initial_call=True,
)
def handle_login(n_clicks, n_submit, email, password):
    if not (n_clicks or n_submit):
        raise dash.exceptions.PreventUpdate

    if not email or not password:
        return (dash.no_update, "Please enter both email and password", "warning", True, dash.no_update, None)

    email_norm = (email or "").strip().lower()
    if auth_db.verify_user(email_norm, password):
        user = auth_db.get_user_by_email(email_norm)
        session_id = session_manager.create_session(email_norm, user["role"])
        redirect_path = _first_allowed_href(path_exists(), user.get("role"))

        return (
            {"session_id": session_id, "role": user["role"], "email": email_norm, "login_time": datetime.now().isoformat()},
            f"Welcome back, {email_norm}!",
            "success",
            True,
            redirect_path,
            None,
        )



    return (dash.no_update, "Invalid email or password.", "danger", True, dash.no_update, None)

# Page metadata (hidden from navbar)
metadata = {
    "name": "Login",
    "href": "/login",
    "show": False,
    "show_filter": False,
    "preference_show": False,
    "title": "Login",
}
