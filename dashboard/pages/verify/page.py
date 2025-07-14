from dash import State, html
import dash_bootstrap_components as dbc

from dash import Input, Output


from dashboard.server_instance import get_app

from excel_manager import update_path_to_excel

app = get_app()

layout = dbc.Modal(
    id="status-modal",
    is_open=True,
    fade=True,
    centered=True,
    backdrop="static",
    keyboard=False,
    children=[
        dbc.ModalHeader("Status", close_button=False),
        dbc.ModalBody(
            [
                dbc.Label("Path to excel :", html_for="url_input"),
                dbc.Input(id="url_input"),
                dbc.Alert(id="status_alert", is_open=False),
            ]
        ),
        dbc.ModalFooter(
            [
                dbc.Button(
                    "Cancel", id="cancel_button", color="secondary", outline=True
                ),
                dbc.Button("Save", id="save_button"),
            ]
        ),
    ],
)


@app.callback(
    [
        Output("status_alert", "is_open"),
        Output("save_button", "color"),
        Output("url_input", "value"),
        Output("status_alert", "children"),
    ],
    [Input("cancel_button", "n_clicks")],
)
def reset_input(_):
    return False, "primary", "", ""


@app.callback(
    Output("status_alert", "children", allow_duplicate=True),
    Output("status_alert", "is_open", allow_duplicate=True),
    Output("status_alert", "color"),
    [
        Output("save_button", "color", allow_duplicate=True),
    ],
    [Input("save_button", "n_clicks")],
    [State("url_input", "value")],
    prevent_initial_call=True,
)
def save_input(_, input_value):

    success, status = update_path_to_excel(input_value)
    print(status)
    color = "success" if success else "danger"

    return status, success, color, color
