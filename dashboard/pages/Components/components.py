import polars as pl
from pathlib import Path
from datetime import datetime, timedelta
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
import json
from server_instance import get_app
import excel_manager

app = get_app()

# Lazy read once
df_lazy = excel_manager.df

# Normalise column names
col_map = {
    c: "_".join(c.strip().split()).upper() for c in df_lazy.collect_schema().names()
}
df_lazy = df_lazy.rename(col_map)

# Ensure DEP_DAY_SCHED is properly formatted as date
df_lazy = df_lazy.with_columns(pl.col("DEP_DAY_SCHED").cast(pl.Date).alias("DEP_DATE"))

# Keep only delay-code rows with TEC description
df_filtered = df_lazy.filter(pl.col("LIB_CODE_DR") == "TEC").collect()


# Dropdown lists
flottes = (
    sorted(df_filtered.get_column("AC_SUBTYPE").drop_nulls().unique().to_list())
    if not df_filtered.is_empty()
    else []
)
matricules = (
    sorted(df_filtered.get_column("AC_REGISTRATION").drop_nulls().unique().to_list())
    if not df_filtered.is_empty()
    else []
)
codes_dr = (
    sorted(df_filtered.get_column("CODE_DR").drop_nulls().unique().to_list())
    if not df_filtered.is_empty()
    else []
)

# Date input bounds
if not df_filtered.is_empty():
    dt_min, dt_max = (
        df_filtered.get_column("DEP_DATE").min(),
        df_filtered.get_column("DEP_DATE").max(),
    )
else:
    dt_min = dt_max = datetime.now().date()

dt_min = dt_min or datetime.now().date()
dt_max = dt_max or datetime.now().date()
dt_min_iso, dt_max_iso = (
    dt_min.strftime("%Y-%m-%d"),
    dt_max.strftime("%Y-%m-%d"),
)
