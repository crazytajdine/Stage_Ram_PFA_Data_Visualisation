# dashboard/pages/login/page.py
from dash import html
import dash_bootstrap_components as dbc


from server_instance import get_app


from dash import Input, Output, State, no_update
import logging

from components.auth import add_output_auth_token, add_output_user_id
from services import user_service, session_service
from data_managers.database_manager import session_scope
from utils_dashboard.utils_authentication import verify_password

app = get_app()


layout = html.Div(
    className="ram-login-page",  # centering only; keeps your existing page bg
    children=[
        dbc.Container(
            fluid=True,
            className="ram-login-wrap",
            children=[
                dbc.Card(
                    body=True,
                    className="ram-login-card ram-login-card--wide",  # large Google-like card
                    children=[
                        # ╭──────────────────── 2-column grid inside the card ────────────────────╮
                        html.Div(
                            className="ram-card-grid",
                            children=[
                                # LEFT: logo + title + subtitle (like Google)
                                html.Div(
                                    className="ram-card-left",
                                    children=[
                                        html.Img(
                                            src=app.get_asset_url("logo_ram-2.png"),
                                            alt="Royal Air Maroc",
                                            className="ram-login-logo",
                                        ),
                                        html.H2("Sign in", className="ram-sign-title"),
                                        html.P(
                                            "Use your RAM account",
                                            className="ram-sign-subtitle",
                                        ),
                                    ],
                                ),
                                # RIGHT: form (keep your IDs/callbacks)
                                html.Div(
                                    className="ram-card-right",
                                    children=[
                                        dbc.Label(
                                            "Email",
                                            html_for="login-email",
                                            className="ram-field-label",
                                        ),
                                        dbc.Input(
                                            id="login-email",
                                            type="email",
                                            placeholder="name@example.com",
                                            className="ram-input",
                                            autoComplete="username",
                                        ),
                                        dbc.Label(
                                            "Password",
                                            html_for="login-password",
                                            className="ram-field-label mt-4",
                                        ),
                                        dbc.Input(
                                            id="login-password",
                                            type="password",
                                            placeholder="••••••••",
                                            className="ram-input",
                                            autoComplete="current-password",
                                        ),
                                        html.Div(
                                            id="login-message",
                                            className="ram-login-message",
                                        ),
                                        html.Div(
                                            dbc.Button(
                                                "Sign in",
                                                id="login-submit",
                                                n_clicks=0,
                                                className="ram-btn-primary",
                                            ),
                                            className="ram-actions",
                                        ),
                                        html.Div(
                                            "Contact your administrator for access",
                                            className="ram-locale",
                                        ),
                                    ],
                                ),
                            ],
                        ),
                        # ╰──────────────────────────────────────────────────────────────────────╯
                    ],
                ),
            ],
        )
    ],
)


@app.callback(
    [
        add_output_auth_token(),
        add_output_user_id(),
        Output("login-message", "children"),  # was: login-alert
        Output("login-message", "is_open"),  # was: login-alert
        Output("login-message", "color"),  # was: login-alert
    ],
    Input("login-submit", "n_clicks"),  # was: login-button
    State("login-email", "value"),
    State("login-password", "value"),
    prevent_initial_call=True,
)
def handle_login(n_clicks, email, password):

    if not email or not password:
        return None, None, "Please fill in all fields", True, "danger"

    with session_scope() as session:
        user: user_service.User = user_service.get_user_by_email_with_password(
            email, session
        )

        # 1) User exists?
        if not user:
            logging.warning(f"Login failed: no user with email {email}")
            return None, None, "Invalid email or password", True, "danger"

        # 2) Disabled flag?
        if getattr(user, "disabled", False):
            logging.warning(f"Login blocked: disabled account for {email}")
            return (
                None,
                None,
                "Your account is disabled. Please contact an administrator.",
                True,
                "danger",
            )

        # 3) Password check
        if not verify_password(password, user.password):
            logging.warning(f"Login failed: wrong password for {email}")
            # fixed: return the correct number of outputs
            return no_update, no_update, "Invalid email or password", True, "danger"

        # 4) Create session
        new_session = session_service.create_session(user.id, session)
        logging.info(
            f"User {email} logged in successfully with session {new_session.id}"
        )

        return (
            new_session.id,
            user.id,
            "Login successful",
            True,
            "success",
        )
