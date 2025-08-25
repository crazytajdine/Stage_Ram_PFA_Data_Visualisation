from dash import html
import dash_bootstrap_components as dbc

layout = dbc.Container(
    dbc.Row(
        dbc.Col(
            dbc.Card(
                [
                    # Card header: spinner next to the title
                    dbc.CardHeader(
                        dbc.Row(
                            [
                                dbc.Col(
                                    dbc.Spinner(
                                        color="primary", type="border", fullscreen=False
                                    ),
                                    width="auto",
                                    className="d-flex align-items-center justify-content-center me-3",
                                ),
                                dbc.Col(
                                    html.H4(
                                        "Couldn't load the Excel file",
                                        className="mb-0 fw-bold",
                                    ),
                                    className="d-flex align-items-center justify-content-start",
                                ),
                            ],
                            align="center",
                            justify="start",
                            className="g-3",
                        )
                    ),
                    # Card body: left-aligned nested style bullets
                    dbc.CardBody(
                        [
                            html.H5("Possible problems:", className="fw-bold"),
                            html.Div(
                                [
                                    html.Div(
                                        "• path might be wrong",
                                        style={
                                            "marginLeft": "1rem",
                                            "marginBottom": "0.5rem",
                                        },
                                    ),
                                    html.Div(
                                        "• excel file might be empty",
                                        style={
                                            "marginLeft": "1rem",
                                            "marginBottom": "0.5rem",
                                        },
                                    ),
                                    html.Div(
                                        "• excel file might contain only bad informations that is not going to be used in this program (without delay flights, all affretements)",
                                        style={"marginLeft": "1rem"},
                                    ),
                                ]
                            ),
                        ]
                    ),
                ],
                className="border border-secondary rounded",
                style={"width": "100%"},
            ),
            width=12,
            className="d-flex justify-content-center",
        ),
        align="center",
        justify="center",
        style={"minHeight": "60vh"},
    ),
    fluid=True,
    style={"width": "80%", "margin": "0 auto"},
)
