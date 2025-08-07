from dash import html

import dash_bootstrap_components as dbc


layout = dbc.Modal(
    [
        dbc.ModalBody(
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Spinner(color="primary", type="border", fullscreen=False),
                        width="auto",
                    ),
                    dbc.Col(
                        html.Div("No File is Found", className="ms-3 fs-4 fw-bold"),
                        width="auto",
                    ),
                ],
                align="center",
                justify="center",
            )
        ),
    ],
    id="id-no-file-modal",
    is_open=True,
    centered=True,
    backdrop="static",
)
