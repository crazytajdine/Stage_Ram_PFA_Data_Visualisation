# dashboard/pages/login/page.py
from dash import html, dcc
import dash_bootstrap_components as dbc


from server_instance import get_app


from dash import Input, Output, State, no_update
import logging

from components.auth import add_output_auth_token
from services import user_service, session_service
from data_managers.database_manager import session_scope
from utils_dashboard.utils_authentication import verify_password

app = get_app()


layout = html.Div(
    [
        # Background with gradient
        html.Div(
            style={
                "position": "fixed",
                "top": 0,
                "left": 0,
                "right": 0,
                "bottom": 0,
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
                                            style={
                                                "height": "120px",
                                                "display": "block",
                                                "margin": "0 auto 20px",
                                            },
                                        ),
                                        html.H3(
                                            "Delay Dashboard",
                                            className="text-center mb-0",
                                        ),
                                        html.P(
                                            "Royal Air Maroc",
                                            className="text-center text-muted mb-4",
                                        ),
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
                                                            [
                                                                html.I(
                                                                    className="bi bi-envelope me-2"
                                                                ),
                                                                "Email Address",
                                                            ],
                                                            html_for="login-email",
                                                        ),
                                                        dbc.Input(
                                                            id="login-email",
                                                            type="email",
                                                            placeholder="user@royalair.ma",
                                                            className="form-control-lg",
                                                            autoFocus=True,
                                                        ),
                                                        dbc.FormText(
                                                            "Must be a valid email address"
                                                        ),
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
                                                            [
                                                                html.I(
                                                                    className="bi bi-lock me-2"
                                                                ),
                                                                "Password",
                                                            ],
                                                            html_for="login-password",
                                                        ),
                                                        dbc.Input(
                                                            id="login-password",
                                                            type="password",
                                                            placeholder="Enter your password",
                                                            className="form-control-lg",
                                                        ),
                                                        dbc.FormText(
                                                            "Minimum 8 characters"
                                                        ),
                                                    ],
                                                    className="mb-4",
                                                )
                                            )
                                        ),
                                        dbc.Row(
                                            dbc.Col(
                                                dbc.Button(
                                                    [
                                                        html.I(
                                                            className="bi bi-box-arrow-in-right me-2"
                                                        ),
                                                        "Sign In",
                                                    ],
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
                                dbc.Alert(
                                    id="login-alert",
                                    is_open=False,
                                    dismissable=True,
                                    className="mt-3",
                                ),
                                # Footer info
                                html.Div(
                                    [
                                        html.Hr(className="mt-4"),
                                        html.P(
                                            [
                                                html.I(
                                                    className="bi bi-info-circle me-2"
                                                ),
                                                "Contact your administrator for access",
                                            ],
                                            className="text-center text-muted small mb-0",
                                        ),
                                    ]
                                ),
                            ]
                        ),
                        className="shadow-lg",
                        style={
                            "maxWidth": "450px",
                            "borderRadius": "15px",
                            "border": "none",
                        },
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
        dcc.Loading(
            id="login-loading",
            type="circle",
            children=html.Div(id="login-loading-output"),
        ),
    ]
)


@app.callback(
    [
        add_output_auth_token(),
        Output("login-alert", "children"),
        Output("login-alert", "is_open"),
        Output("login-alert", "color"),
    ],
    Input("login-button", "n_clicks"),
    State("login-email", "value"),
    State("login-password", "value"),
    prevent_initial_call=True,
)
def handle_login(n_clicks, email, password):
    if not email or not password:
        return no_update, "Please fill in all fields", True, "danger"

    with session_scope() as session:
        user: user_service.User = user_service.get_user_by_email_with_password(email, session)

        # 1) User exists?
        if not user:
            logging.warning(f"Login failed: no user with email {email}")
            return no_update, "Invalid email or password", True, "danger"

        # 2) Disabled flag check (boolean column on users table)
        #    If your field name differs, replace `disabled` below.
        if getattr(user, "disabled", False):
            logging.warning(f"Login blocked: disabled account for {email}")
            return no_update, "Your account is disabled. Please contact an administrator.", True, "danger"

        # (Optional) If you also keep a disabled flag on the role, uncomment:
        # if getattr(getattr(user, "role", None), "disabled", False):
        #     logging.warning(f"Login blocked: disabled role for user {email}")
        #     return no_update, "Your role is disabled. Please contact an administrator.", True, "danger"

        # 3) Password check
        if not verify_password(password, user.password):
            logging.warning(f"Login failed: wrong password for {email}")
            return no_update, "Invalid email or password", True, "danger"

        # 4) Create session
        new_session = session_service.create_session(user.id, session)
        logging.info(f"User {email} logged in successfully with session {new_session.id}")

        return (
            new_session.id,          # auth token/id
            "Login successful",      # alert text
            True,                    # is_open
            "success",               # color
        )

