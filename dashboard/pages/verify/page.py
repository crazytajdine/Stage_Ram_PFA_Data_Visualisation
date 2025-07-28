from dash import Input, Output, State
import dash
from server_instance import get_app
from excel_manager import update_path_to_excel, ID_PATH_STORE
import dash_bootstrap_components as dbc

app = None

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
                dbc.Label("Path to Excel:", html_for="url_input"),
                dbc.Input(id="url_input", type="text"),
                dbc.Alert(id="status_alert", is_open=False),
            ]
        ),
        dbc.ModalFooter(
            [
                dbc.Button(
                    "Cancel",
                    id="cancel_button",
                    type="reset",
                    color="secondary",
                    outline=True,
                ),
                dbc.Button("Save", id="save_button", type="submit", color="primary"),
            ]
        ),
    ],
)


# @app.callback(
#     [
#         Output("status_alert", "is_open"),
#         Output("save_button", "color"),
#         Output("url_input", "value"),
#         Output("status_alert", "children"),
#     ],
#     Input("cancel_button", "n_clicks"),
#     prevent_initial_call=True,
# )
def reset_input(_):
    print("Resetting input value")
    return False, "primary", "", ""


# @app.callback(
#     [
#         Output("status_alert", "children", allow_duplicate=True),
#         Output("status_alert", "is_open", allow_duplicate=True),
#         Output("status_alert", "color"),
#         Output("save_button", "color", allow_duplicate=True),
#         Output(ID_PATH_STORE, "data"),
#     ],
#     Input("save_button", "n_clicks"),
#     State("url_input", "value"),
#     prevent_initial_call=True,
# )
def save_input(n_clicks, input_value):

    if not n_clicks:
        raise dash.exceptions.PreventUpdate

    print("Saving input value:", input_value)

    success, message = update_path_to_excel(input_value)
    print("Result:", message)

    alert_color = "success" if success else "danger"
    new_value = input_value if success else dash.no_update

    return message, True, alert_color, alert_color, new_value
