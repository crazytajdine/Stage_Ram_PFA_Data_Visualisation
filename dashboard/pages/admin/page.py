# dashboard/pages/admin/page.py
from dash import html, dcc, Input, Output, State, callback, dash_table, no_update
import dash_bootstrap_components as dbc
from server_instance import get_app
from dashboard.state import session_manager
import dash
import plotly.graph_objs as go
from datetime import datetime, timedelta
import typing as t

from configurations.nav_config import build_nav_items_meta
from data_managers.excel_manager import path_exists

app = get_app()


# ---------- Helpers ----------
def _fmt_dt(value: t.Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M")
    try:
        return datetime.fromisoformat(str(value)).strftime("%Y-%m-%d %H:%M")
    except Exception:
        return str(value)


def _format_users_table_data() -> list[dict]:
    users = auth_db.get_all_users()
    for u in users:
        u["status"] = "Active" if u.get("is_active") else "Inactive"
        u["created_at"] = _fmt_dt(u.get("created_at"))
    return users


def _norm_href(h: str | None) -> str:
    """
    Canonicalize to leading '/', no trailing '/', lowercase.
    Works for both slugs ('performance-metrics') and hrefs ('/performance-metrics/').
    """
    p = (h or "/").split("?")[0].split("#")[0].strip()
    if not p.startswith("/"):
        p = "/" + p
    p = "/" + p.lstrip("/").rstrip("/")
    return p.lower()


def _all_page_options() -> list[dict]:
    """
    Build checklist options with VALUE = canonical href (e.g. '/performance-metrics').
    Labels keep the friendly name + href for clarity.
    """
    meta = build_nav_items_meta(path_exists()) or []
    opts = []
    seen = set()
    for m in meta:
        href = _norm_href(m.href)
        if href == "/admin":  # admin reserved
            continue
        label = getattr(m, "name", None) or href.lstrip("/") or "home"
        if href not in seen:
            seen.add(href)
            opts.append({"label": f"{label} ({href})", "value": href})
    return opts


# ---------- Layout ----------
layout = dbc.Container(
    [
        # Header
        dbc.Row([dbc.Col([html.H1("Admin Dashboard", className="mb-2"), html.Hr()])]),
        # Stats
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.H4("Total Users", className="text-muted mb-1"),
                                html.H2(
                                    id="total-users-count",
                                    className="text-primary mb-0",
                                ),
                            ]
                        ),
                        className="text-center",
                    ),
                    md=3,
                ),
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.H4("Active Users", className="text-muted mb-1"),
                                html.H2(
                                    id="active-users-count",
                                    className="text-success mb-0",
                                ),
                            ]
                        ),
                        className="text-center",
                    ),
                    md=3,
                ),
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.H4("Admin Users", className="text-muted mb-1"),
                                html.H2(
                                    id="admin-users-count",
                                    className="text-warning mb-0",
                                ),
                            ]
                        ),
                        className="text-center",
                    ),
                    md=3,
                ),
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.H4("Recent Logins", className="text-muted mb-1"),
                                html.H2(
                                    id="recent-logins-count", className="text-info mb-0"
                                ),
                            ]
                        ),
                        className="text-center",
                    ),
                    md=3,
                ),
            ],
            className="mb-4",
        ),
        # Create user (role comes from roles list)
        dbc.Card(
            [
                dbc.CardHeader(html.H4("Create New User", className="mb-0")),
                dbc.CardBody(
                    [
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        dbc.Label(
                                            "Email Address", html_for="new-user-email"
                                        ),
                                        dbc.Input(
                                            id="new-user-email",
                                            type="email",
                                            placeholder="user@royalair.ma",
                                            className="mb-1",
                                        ),
                                        dbc.FormText("Must be a valid email address"),
                                    ],
                                    md=4,
                                ),
                                dbc.Col(
                                    [
                                        dbc.Label(
                                            "Password", html_for="new-user-password"
                                        ),
                                        dbc.Input(
                                            id="new-user-password",
                                            type="password",
                                            placeholder="Strong password",
                                            className="mb-1",
                                        ),
                                        dbc.FormText("Minimum 8 characters"),
                                    ],
                                    md=4,
                                ),
                                dbc.Col(
                                    [
                                        dbc.Label(
                                            "System Role", html_for="new-user-role"
                                        ),
                                        dbc.Select(
                                            id="new-user-role",
                                            options=[],
                                            placeholder="Choose role",
                                        ),
                                        dbc.FormText("Roles are defined below"),
                                    ],
                                    md=4,
                                ),
                            ]
                        ),
                        dbc.Row(
                            [
                                dbc.Col(
                                    dbc.Button(
                                        [
                                            html.I(className="bi bi-plus-circle me-2"),
                                            "Create User",
                                        ],
                                        id="create-user-btn",
                                        color="primary",
                                        className="w-100 mt-2",
                                    )
                                )
                            ]
                        ),
                        dbc.Alert(
                            id="create-user-alert",
                            is_open=False,
                            dismissable=True,
                            className="mt-3",
                        ),
                    ]
                ),
            ],
            className="mb-4",
        ),
        # Roles & Permissions
        dbc.Card(
            [
                dbc.CardHeader(html.H4("Roles & Page Permissions", className="mb-0")),
                dbc.CardBody(
                    [
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        dbc.Label("Create New Role"),
                                        dbc.Input(
                                            id="new-role-name",
                                            placeholder="e.g., perf, ops, finance",
                                        ),
                                    ],
                                    md=4,
                                ),
                                dbc.Col(
                                    [
                                        dbc.Button(
                                            [
                                                html.I(
                                                    className="bi bi-plus-square me-2"
                                                ),
                                                "Create Role",
                                            ],
                                            id="create-role-btn",
                                            color="secondary",
                                            className="mt-4 w-100",
                                        ),
                                    ],
                                    md=2,
                                ),
                                dbc.Col(
                                    [
                                        dbc.Label("Select Role"),
                                        dbc.Select(
                                            id="perm-role-select",
                                            options=[],
                                            placeholder="Choose a role",
                                        ),
                                    ],
                                    md=3,
                                ),
                                dbc.Col(
                                    [
                                        dbc.Button(
                                            [
                                                html.I(className="bi bi-trash me-2"),
                                                "Delete Role",
                                            ],
                                            id="delete-role-btn",
                                            color="danger",
                                            className="mt-4 w-100",
                                        ),
                                    ],
                                    md=3,
                                ),
                            ],
                            className="mb-3",
                        ),
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        dbc.Label("Allowed Pages for Selected Role"),
                                        dcc.Checklist(
                                            id="perm-pages-checklist",
                                            options=[],
                                            value=[],
                                            labelStyle={"display": "block"},
                                        ),
                                        dbc.Button(
                                            [
                                                html.I(className="bi bi-save2 me-2"),
                                                "Save Permissions",
                                            ],
                                            id="save-perms-btn",
                                            color="primary",
                                            className="mt-3",
                                        ),
                                    ],
                                    md=6,
                                ),
                            ]
                        ),
                        dbc.Alert(
                            id="roles-alert",
                            is_open=False,
                            dismissable=True,
                            className="mt-3",
                        ),
                    ]
                ),
            ],
            className="mb-4",
        ),
        # Users table + actions + assign role
        dbc.Card(
            [
                dbc.CardHeader(
                    [
                        dbc.Row(
                            [
                                dbc.Col(
                                    html.H4("User Management", className="mb-0"), md=4
                                ),
                                dbc.Col(
                                    dbc.InputGroup(
                                        [
                                            dbc.InputGroupText(
                                                html.I(className="bi bi-search")
                                            ),
                                            dbc.Input(
                                                id="user-search",
                                                placeholder="Search email or role...",
                                                type="text",
                                            ),
                                        ],
                                        size="sm",
                                    ),
                                    md=4,
                                ),
                                dbc.Col(
                                    dbc.Button(
                                        [
                                            html.I(
                                                className="bi bi-arrow-clockwise me-2"
                                            ),
                                            "Refresh",
                                        ],
                                        id="refresh-users-btn",
                                        color="secondary",
                                        size="sm",
                                        className="w-100",
                                    ),
                                    md=2,
                                ),
                                dbc.Col(
                                    dbc.ButtonGroup(
                                        [
                                            dbc.Button(
                                                "Enable",
                                                id="btn-enable",
                                                color="success",
                                                size="sm",
                                            ),
                                            dbc.Button(
                                                "Disable",
                                                id="btn-disable",
                                                color="warning",
                                                size="sm",
                                            ),
                                            dbc.Button(
                                                "Delete",
                                                id="btn-delete",
                                                color="danger",
                                                size="sm",
                                            ),
                                        ],
                                        className="w-100",
                                    ),
                                    md=2,
                                ),
                            ]
                        )
                    ]
                ),
                dbc.CardBody(
                    [
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        dbc.Label("Assign Role to Selected User"),
                                        dbc.InputGroup(
                                            [
                                                dbc.Select(
                                                    id="assign-role-select",
                                                    options=[],
                                                    placeholder="Choose role",
                                                ),
                                                dbc.Button(
                                                    "Assign",
                                                    id="assign-role-btn",
                                                    color="primary",
                                                ),
                                            ],
                                            className="mb-2",
                                        ),
                                    ],
                                    md=5,
                                ),
                            ]
                        ),
                        dbc.Alert(
                            id="user-action-alert",
                            is_open=False,
                            dismissable=True,
                            className="mb-3",
                        ),
                        dash_table.DataTable(
                            id="users-table",
                            columns=[
                                {"name": "ID", "id": "id", "type": "numeric"},
                                {"name": "Email", "id": "email", "type": "text"},
                                {"name": "Role", "id": "role", "type": "text"},
                                {"name": "Status", "id": "status", "type": "text"},
                                {
                                    "name": "Created At",
                                    "id": "created_at",
                                    "type": "text",
                                },
                                {
                                    "name": "Created By",
                                    "id": "created_by",
                                    "type": "text",
                                },
                            ],
                            data=[],
                            row_selectable="single",
                            sort_action="native",
                            filter_action="native",
                            page_action="native",
                            page_size=10,
                            style_cell={
                                "textAlign": "left",
                                "padding": "10px",
                                "whiteSpace": "normal",
                                "height": "auto",
                            },
                            style_data_conditional=[
                                {
                                    "if": {
                                        "column_id": "role",
                                        "filter_query": '{role} = "admin"',
                                    },
                                    "backgroundColor": "#fff3cd",
                                    "fontWeight": "bold",
                                },
                                {
                                    "if": {
                                        "column_id": "status",
                                        "filter_query": '{status} = "Inactive"',
                                    },
                                    "backgroundColor": "#f8d7da",
                                    "color": "#721c24",
                                },
                                {
                                    "if": {
                                        "column_id": "status",
                                        "filter_query": '{status} = "Active"',
                                    },
                                    "backgroundColor": "#d4edda",
                                    "color": "#155724",
                                },
                            ],
                            style_header={
                                "backgroundColor": "rgb(230,230,230)",
                                "fontWeight": "bold",
                            },
                        ),
                        dbc.Modal(
                            [
                                dbc.ModalHeader("Confirm Action"),
                                dbc.ModalBody(id="confirm-modal-body"),
                                dbc.ModalFooter(
                                    [
                                        dbc.Button(
                                            "Cancel",
                                            id="cancel-action-btn",
                                            color="secondary",
                                        ),
                                        dbc.Button(
                                            "Confirm",
                                            id="confirm-action-btn",
                                            color="danger",
                                        ),
                                    ]
                                ),
                            ],
                            id="confirm-modal",
                            is_open=False,
                        ),
                    ]
                ),
            ]
        ),
        # Login Activity (placeholder)
        dbc.Card(
            [
                dbc.CardHeader("Login Activity (Last 7 Days)"),
                dbc.CardBody([dcc.Graph(id="login-activity-chart")]),
            ],
            className="mt-4",
        ),
        dcc.Store(id="pending-action-store"),
        dcc.Store(id="rbac-refresh"),
        dcc.Interval(id="users-interval", interval=30_000),
    ],
    fluid=True,
    className="p-4",
)

# # ---------- Callbacks ----------
# @callback(
#     Output("total-users-count", "children"),
#     Output("active-users-count", "children"),
#     Output("admin-users-count", "children"),
#     Output("recent-logins-count", "children"),
#     Input("users-interval", "n_intervals"),
# )
# def update_stats(_n):
#     users = auth_db.get_all_users()
#     total = len(users)
#     active = sum(1 for u in users if u.get("is_active"))
#     admins = sum(1 for u in users if u.get("role") == "admin")
#     try:
#         sess_counts = session_manager.get_active_sessions_count()
#         recent = sess_counts.get("total", 0)
#     except Exception:
#         recent = 0
#     return total, active, admins, recent

# # load roles and pages (instant refresh via rbac-refresh)
# @callback(
#     Output("new-user-role", "options"),
#     Output("assign-role-select", "options"),
#     Output("perm-role-select", "options"),
#     Output("perm-pages-checklist", "options"),
#     Input("users-interval", "n_intervals"),
#     Input("rbac-refresh", "data"),
# )
# def load_roles_and_pages(_n, _refresh):
#     roles = auth_db.list_roles()
#     role_opts = [{"label": r, "value": r} for r in roles]
#     return role_opts, role_opts, role_opts, _all_page_options()

# # Create user
# @callback(
#     Output("create-user-alert", "children"),
#     Output("create-user-alert", "color"),
#     Output("create-user-alert", "is_open"),
#     Output("new-user-email", "value"),
#     Output("new-user-password", "value"),
#     Output("users-table", "data", allow_duplicate=True),
#     Input("create-user-btn", "n_clicks"),
#     State("new-user-email", "value"),
#     State("new-user-password", "value"),
#     State("new-user-role", "value"),
#     State("session-store", "data"),
#     prevent_initial_call=True,
# )
# def create_user(n_clicks, email, password, role, session_data):
#     if not n_clicks:
#         raise dash.exceptions.PreventUpdate
#     email_norm = (email or "").lower().strip()
#     if not email_norm or not password or not role:
#         return "Please fill all fields", "warning", True, email, password, no_update
#     if "@" not in email_norm:
#         return "Please enter a valid email address", "warning", True, email, password, no_update
#     if len(password) < 8:
#         return "Password must be at least 8 characters", "warning", True, email, password, no_update
#     try:
#         creator_email = (session_data or {}).get("email") or "system"
#         auth_db.create_user(email_norm, password, role, creator_email)
#         users_data = _format_users_table_data()
#         return (f"User {email_norm} created successfully!", "success", True, "", "", users_data)
#     except Exception as e:
#         msg = str(e)
#         if "UNIQUE" in msg or "unique" in msg:
#             return "This email is already registered", "danger", True, email, password, no_update
#     # generic error
#         return f"Error: {e}", "danger", True, email, password, no_update

# # Refresh table
# @callback(
#     Output("users-table", "data"),
#     Input("refresh-users-btn", "n_clicks"),
#     Input("users-interval", "n_intervals"),
# )
# def refresh_users_table(_n_clicks, _n_int):
#     return _format_users_table_data()

# # Search
# @callback(
#     Output("users-table", "filter_query"),
#     Input("user-search", "value"),
# )
# def apply_search_filter(q):
#     if not q:
#         return ""
#     q = q.replace('"', r'\"')
#     return f'{{email}} contains "{q}" || {{role}} contains "{q}" || {{status}} contains "{q}"'

# # Open confirm modal
# @callback(
#     Output("confirm-modal", "is_open"),
#     Output("confirm-modal-body", "children"),
#     Output("pending-action-store", "data"),
#     Output("user-action-alert", "children"),
#     Output("user-action-alert", "color"),
#     Output("user-action-alert", "is_open"),
#     Input("btn-enable", "n_clicks"),
#     Input("btn-disable", "n_clicks"),
#     Input("btn-delete", "n_clicks"),
#     State("users-table", "selected_rows"),
#     State("users-table", "data"),
#     prevent_initial_call=True,
# )
# def open_action_modal(n_en, n_dis, n_del, selected_rows, data):
#     trig = dash.ctx.triggered_id
#     if not trig:
#         raise dash.exceptions.PreventUpdate
#     if not selected_rows:
#         return False, no_update, no_update, "Select a user first.", "warning", True
#     row_idx = selected_rows[0]
#     user = data[row_idx]
#     action = "enable" if trig == "btn-enable" else "disable" if trig == "btn-disable" else "delete"
#     body = f"Are you sure you want to {action} user: {user['email']} (id={user['id']})?"
#     pending = {"action": action, "user_id": user["id"], "email": user["email"]}
#     return True, body, pending, no_update, no_update, False

# # Confirm / cancel action
# @callback(
#     Output("confirm-modal", "is_open", allow_duplicate=True),
#     Output("users-table", "data", allow_duplicate=True),
#     Output("user-action-alert", "children", allow_duplicate=True),
#     Output("user-action-alert", "color", allow_duplicate=True),
#     Output("user-action-alert", "is_open", allow_duplicate=True),
#     Input("confirm-action-btn", "n_clicks"),
#     Input("cancel-action-btn", "n_clicks"),
#     State("pending-action-store", "data"),
#     prevent_initial_call=True,
# )
# def perform_action(n_confirm, n_cancel, pending):
#     if dash.ctx.triggered_id == "cancel-action-btn":
#         return False, no_update, no_update, no_update, False
#     if not n_confirm or not pending:
#         raise dash.exceptions.PreventUpdate
#     user_id = pending.get("user_id")
#     email = pending.get("email")
#     action = pending.get("action")
#     try:
#         if action == "enable":
#             auth_db.set_active(user_id, True)
#             msg, color = f"User {email} enabled.", "success"
#         elif action == "disable":
#             auth_db.set_active(user_id, False)
#             msg, color = f"User {email} disabled.", "warning"
#         else:
#             auth_db.delete_user(user_id)
#             msg, color = f"User {email} deleted.", "danger"
#         users_data = _format_users_table_data()
#         return False, users_data, msg, color, True
#     except Exception as e:
#         return False, no_update, f"Action failed: {e}", "danger", True

# # Assign role to selected user
# @callback(
#     Output("users-table", "data", allow_duplicate=True),
#     Output("user-action-alert", "children", allow_duplicate=True),
#     Output("user-action-alert", "color", allow_duplicate=True),
#     Output("user-action-alert", "is_open", allow_duplicate=True),
#     Input("assign-role-btn", "n_clicks"),
#     State("assign-role-select", "value"),
#     State("users-table", "selected_rows"),
#     State("users-table", "data"),
#     prevent_initial_call=True,
# )
# def assign_role(n, role, selected_rows, data):
#     if not n:
#         raise dash.exceptions.PreventUpdate
#     if not selected_rows:
#         return no_update, "Select a user first.", "warning", True
#     if not role:
#         return no_update, "Choose a role to assign.", "warning", True
#     row_idx = selected_rows[0]
#     user = data[row_idx]
#     try:
#         auth_db.assign_user_role(user["id"], role)
#         users_data = _format_users_table_data()
#         return users_data, f"Role '{role}' assigned to {user['email']}.", "success", True
#     except Exception as e:
#         return no_update, f"Error: {e}", "danger", True

# # Role creation / deletion (instant refresh via rbac-refresh ping)
# @callback(
#     Output("roles-alert", "children"),
#     Output("roles-alert", "color"),
#     Output("roles-alert", "is_open"),
#     Output("perm-role-select", "value"),
#     Output("new-role-name", "value"),
#     Output("rbac-refresh", "data"),
#     Input("create-role-btn", "n_clicks"),
#     Input("delete-role-btn", "n_clicks"),
#     State("new-role-name", "value"),
#     State("perm-role-select", "value"),
#     prevent_initial_call=True,
# )
# def create_or_delete_role(n_add, n_del, new_role, selected_role):
#     import time
#     trig = dash.ctx.triggered_id
#     try:
#         if trig == "create-role-btn":
#             r = (new_role or "").strip().lower()
#             if not r:
#                 return "Role name is required.", "warning", True, dash.no_update, new_role, dash.no_update
#             auth_db.create_role(r, "admin-ui")
#             return f"Role '{r}' created.", "success", True, r, "", time.time()
#         elif trig == "delete-role-btn":
#             r = (selected_role or "").strip().lower()
#             if not r:
#                 return "Select a role to delete.", "warning", True, dash.no_update, dash.no_update, dash.no_update
#             auth_db.delete_role(r)
#             return f"Role '{r}' deleted.", "success", True, "", dash.no_update, time.time()
#     except Exception as e:
#         return f"Error: {e}", "danger", True, dash.no_update, dash.no_update, dash.no_update
#     raise dash.exceptions.PreventUpdate

# # Load permissions for selected role (normalize for checklist values)
# @callback(
#     Output("perm-pages-checklist", "value"),
#     Input("perm-role-select", "value"),
# )
# def load_role_perms(role):
#     if not role:
#         return []
#     perms = auth_db.get_role_permissions(role) or []
#     # accept legacy slugs and normalize to hrefs so they match options
#     return sorted({_norm_href(v) for v in perms} | {_norm_href("/" + v) for v in perms})

# # Save permissions (store normalized hrefs)
# @callback(
#     Output("roles-alert", "children", allow_duplicate=True),
#     Output("roles-alert", "color", allow_duplicate=True),
#     Output("roles-alert", "is_open", allow_duplicate=True),
#     Output("rbac-refresh", "data", allow_duplicate=True),
#     Input("save-perms-btn", "n_clicks"),
#     State("perm-role-select", "value"),
#     State("perm-pages-checklist", "value"),
#     prevent_initial_call=True,
# )
# def save_perms(n, role, pages):
#     import time
#     if not n:
#         raise dash.exceptions.PreventUpdate
#     if not role:
#         return "Select a role first.", "warning", True, no_update
#     try:
#         normalized = sorted({_norm_href(p) for p in (pages or [])})
#         auth_db.set_role_permissions(role, normalized)
#         return "Permissions saved.", "success", True, time.time()
#     except Exception as e:
#         return f"Error: {e}", "danger", True, no_update

# # Login activity placeholder
# @callback(
#     Output("login-activity-chart", "figure"),
#     Input("users-interval", "n_intervals"),
# )
# def update_login_chart(_n):
#     dates = [(datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(6, -1, -1)]
#     counts = [max(0, (i * 3) % 17 + (i % 5)) for i in range(len(dates))]
#     fig = go.Figure()
#     fig.add_bar(x=dates, y=counts, name="Logins")
#     fig.update_layout(title="Daily Login Activity", xaxis_title="Date", yaxis_title="Number of Logins",
#                       showlegend=False, height=300, margin=dict(l=0, r=0, t=30, b=0),
#                       paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
#     fig.update_xaxes(gridcolor="rgba(128,128,128,0.2)")
#     fig.update_yaxes(gridcolor="rgba(128,128,128,0.2)")
#     return fig
