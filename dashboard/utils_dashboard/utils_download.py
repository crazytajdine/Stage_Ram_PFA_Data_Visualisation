import io
import dash
import xlsxwriter
from schemas.filter import FilterType
from utils_dashboard.utils_filter import get_filter_name
import polars as pl
from dash.dcc import send_bytes
from dash import Input, Output, State, dcc
import logging


from server_instance import get_app

logging.info("Excel file uploading...")


ID_DOWNLOAD = "id-download"
download_dash = dcc.Download(id=ID_DOWNLOAD)

app = get_app()


def get_download_trigger():
    return Output(ID_DOWNLOAD, "data", allow_duplicate=True)


import logging


def export_excel(
    df: pl.DataFrame,
    name: str,
    with_filter: bool = True,
) -> None:
    logging.debug("Start export_excel - with_filter=%s", with_filter)

    if with_filter:

        filt = get_filter_name()
        filename = f"{name}_{filt}.xlsx"
    else:
        filename = f"{name}.xlsx"
    logging.info("Name of generate file : %s", filename)

    # Create in-memory workbook
    buffer = io.BytesIO()
    with xlsxwriter.Workbook(buffer, {"in_memory": True}) as wb:
        df.write_excel(workbook=wb)
    buffer.seek(0)

    # Stream back to user
    return send_bytes(lambda stream: stream.write(buffer.getvalue()), filename=filename)


def add_export_callbacks(
    id_table: str, id_button: str, name: str, with_filter: bool = True
):
    logging.debug(
        "Adding Excel export callback for button '%s' and table '%s'.",
        id_button,
        id_table,
    )

    @app.callback(
        get_download_trigger(),
        Input(id_button, "n_clicks"),
        State(id_table, "data", allow_optional=True),
        State(id_table, "columns", allow_optional=True),  # Add column state
        prevent_initial_call=True,
        allow_duplicate=True,
    )
    def export_to_excel(n_clicks, table_data, table_columns):
        print(table_columns)
        print(bool(table_data))
        print(n_clicks)
        if (not n_clicks) or (not table_data) or (not table_columns):
            raise dash.exceptions.PreventUpdate
        print("ff")
        rename_map = {col["id"]: col["name"] for col in table_columns}

        df = pl.DataFrame(table_data).rename(rename_map)

        if df.is_empty():
            raise dash.exceptions.PreventUpdate

        print(f"Exporting {name} to Excel")
        return export_excel(df, name, with_filter)
