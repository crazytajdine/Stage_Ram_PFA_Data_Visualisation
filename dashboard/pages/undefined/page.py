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
                        html.Div(
                            "Either we didn't find a file or it doesn't contain any useful information ...",
                            className="ms-3 fs-4 fw-bold",
                        ),
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
