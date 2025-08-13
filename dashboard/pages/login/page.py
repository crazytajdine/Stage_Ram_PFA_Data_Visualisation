# dashboard/pages/login/page.py
from dash import html, dcc
import dash_bootstrap_components as dbc


from server_instance import get_app


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
