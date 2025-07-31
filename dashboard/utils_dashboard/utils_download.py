import io
import dash
import xlsxwriter
from schemas.filter import FilterType
from utils_dashboard.utils_filter import get_filter_name
import polars as pl
from dash.dcc import send_bytes
from dash import Input, Output, State, dcc

from server_instance import get_app

ID_DOWNLOAD = "id-download"
download_dash = dcc.Download(id=ID_DOWNLOAD)

app = get_app()


def get_download_trigger():
    return Output(ID_DOWNLOAD, "data", allow_duplicate=True)


def export_excel(
    df: pl.DataFrame,
    name: str,
    with_filter: bool = True,
) -> None:

    if with_filter:

        filt = get_filter_name()
        filename = f"{name}_{filt}.xlsx"
    else:
        filename = f"{name}.xlsx"

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

    @app.callback(
        get_download_trigger(),
        Input(id_button, "n_clicks"),
        State(id_table, "data", allow_optional=True),
        prevent_initial_call=True,
        allow_duplicate=True,
    )
    def export_to_excel(n_clicks, table_data):

        if not n_clicks or not table_data:
            raise dash.exceptions.PreventUpdate

        df = pl.DataFrame(table_data)

        if df.is_empty():
            raise dash.exceptions.PreventUpdate
        print(f"Exporting {name} to Excel")

        return export_excel(df, name, with_filter)
