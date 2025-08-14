# dashboard/pages/admin/page.py
from __future__ import annotations

import logging
from datetime import datetime, timedelta
import typing as t

import bcrypt
import dash
from dash import Input, Output, State, html, dcc, dash_table
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import plotly.graph_objs as go

from server_instance import get_app
from data_managers.database_manager import session_scope

from services import user_service, role_service, page_service, session_service

app = get_app()


# ---------- Helpers (robust for ORM models OR Pydantic DTOs) ----------
def _get_attr(obj, *names, default=None):
    for n in names:
        try:
            v = getattr(obj, n)
        except Exception:
            v = None
        if v is not None:
            return v
    return default

def _role_name(u, db_session):
    rn = _get_attr(u, "role", "role_name")
    if rn:
        return rn
    role_id = _get_attr(u, "role_id")
    if role_id:
        r = role_service.get_role_by_id(role_id, db_session)
        if r:
            return _get_attr(r, "role_name", "name", default="No Role")
    return "No Role"

def _creator_email(u, db_session):
    creator_id = _get_attr(u, "created_by", "created_by_id")
    if creator_id:
        creator = user_service.get_user_by_id(creator_id, db_session)
        if creator:
            return _get_attr(creator, "email", default="")
    return ""

def _is_disabled(u):
    return bool(_get_attr(u, "disabled", "is_disabled", default=False))

def _created_at_str(u):
    dt = _get_attr(u, "created_at")
    if not dt:
        return ""
    if isinstance(dt, datetime):
        return dt.strftime("%Y-%m-%d %H:%M")
    try:
        return datetime.fromisoformat(str(dt)).strftime("%Y-%m-%d %H:%M")
    except Exception:
        return str(dt)

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
    Build checklist options.
    VALUE = page name (so page_service.get_page_by_name works)
    LABEL = 'Name (/href)' for clarity.
    """
    try:
        # Lazy import to avoid circular imports at module load time
        from configurations.nav_config import NAV_CONFIG
    except Exception:
        return []

    opts: list[dict] = []
    seen: set[str] = set()

    for m in NAV_CONFIG:
        href = _norm_href(getattr(m, "href", "/"))
        if href == "/admin":  # admin is reserved
            continue
        show_nav = getattr(m, "show_navbar", True)
        pref_show = getattr(m, "preference_show", True)
        if not (show_nav and pref_show):
            continue
        name = getattr(m, "name", None) or href.lstrip("/") or "home"
        if name in seen:
            continue
        seen.add(name)
        opts.append({"label": f"{name} ({href})", "value": name})
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
                                html.H2(id="total-users-count", className="text-primary mb-0"),
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
                                html.H2(id="active-users-count", className="text-success mb-0"),
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
                                html.H2(id="admin-users-count", className="text-warning mb-0"),
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
                                html.H2(id="recent-logins-count", className="text-info mb-0"),
                            ]
                        ),
                        className="text-center",
                    ),
                    md=3,
                ),
            ],
            className="mb-4",
        ),
        # Create user
        dbc.Card(
            [
                dbc.CardHeader(html.H4("Create New User", className="mb-0")),
                dbc.CardBody(
                    [
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        dbc.Label("Email Address", html_for="new-user-email"),
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
                                        dbc.Label("Password", html_for="new-user-password"),
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
                                        dbc.Label("System Role", html_for="new-user-role"),
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
                                        [html.I(className="bi bi-plus-circle me-2"), "Create User"],
                                        id="create-user-btn",
                                        color="primary",
                                        className="w-100 mt-2",
                                    )
                                )
                            ]
                        ),
                        dbc.Alert(id="create-user-alert", is_open=False, dismissable=True, className="mt-3"),
                    ]
                ),
            ],
            className="mb-4",
        ),
        # Create Role with Permissions
        dbc.Card(
            [
                dbc.CardHeader(html.H4("Create Role with Permissions", className="mb-0")),
                dbc.CardBody(
                    [
                        dbc.Row(
                            [
                                dbc.Col(
                                    [dbc.Label("Role name"), dbc.Input(id="new-role-name", placeholder="e.g., perf, ops, finance")],
                                    md=6,
                                ),
                            ],
                            className="g-3 mb-3",
                        ),
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        dbc.Label("Allowed pages"),
                                        dcc.Checklist(
                                            id="perm-pages-checklist",
                                            options=_all_page_options(),
                                            value=[],
                                            labelStyle={"display": "block"},
                                            inputStyle={"marginRight": "8px"},
                                        ),
                                    ],
                                    md=8,
                                ),
                            ],
                            className="g-3",
                        ),
                        html.Div(
                            dbc.Button(
                                [html.I(className="bi bi-shield-plus me-2"), "Create Role"],
                                id="create-role-btn",
                                color="primary",
                                className="w-100 mt-3",
                            ),
                            className="d-flex justify-content-end",
                        ),
                        dbc.Alert(id="roles-alert", is_open=False, dismissable=True, className="mt-3"),
                    ]
                ),
            ],
            className="mb-4",
        ),
        # Edit Role & Permissions
        dbc.Card(
            [
                dbc.CardHeader(html.H4("Edit Role & Permissions", className="mb-0")),
                dbc.CardBody(
                    [
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        dbc.Label("Select role"),
                                        dbc.Select(id="edit-role-select", options=[], placeholder="Choose a role"),
                                        dbc.FormText("Pick a role to view and modify its allowed pages."),
                                    ],
                                    md=6,
                                ),
                            ],
                            className="g-3 mb-3",
                        ),
                        dbc.Label("Allowed pages"),
                        html.Div(
                            dcc.Checklist(
                                id="edit-perm-pages-checklist",
                                options=_all_page_options(),
                                value=[],
                                labelStyle={"display": "block"},
                                inputStyle={"marginRight": "8px"},
                            ),
                            style={
                                "maxHeight": "320px",
                                "overflowY": "auto",
                                "border": "1px solid #e9ecef",
                                "borderRadius": "0.5rem",
                                "padding": "12px",
                                "background": "#fff",
                            },
                            className="mb-2",
                        ),
                        html.Small(["Selected ", html.Span("0", id="edit-pages-count"), " page(s)"], className="text-muted"),
                        dbc.Alert(id="edit-roles-alert", is_open=False, dismissable=True, className="mt-3"),
                    ]
                ),
                dbc.CardFooter(
                    dbc.Row(
                        [
                            dbc.Col(
                                dbc.Button(
                                    [html.I(className="bi bi-save2 me-2"), "Update Permissions"],
                                    id="update-perms-btn",
                                    color="dark",
                                    className="w-100 rounded-0 py-3 text-uppercase fw-semibold",
                                ),
                                className="p-0",
                            ),
                            dbc.Col(
                                dbc.Button(
                                    [html.I(className="bi bi-trash me-2"), "Delete Role"],
                                    id="edit-delete-role-btn",
                                    color="danger",
                                    className="w-100 rounded-0 py-3 text-uppercase fw-semibold",
                                ),
                                className="p-0",
                            ),
                        ],
                        className="g-0",
                    ),
                    className="p-0",
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
                                dbc.Col(html.H4("User Management", className="mb-0"), md=4),
                                dbc.Col(
                                    dbc.InputGroup(
                                        [
                                            dbc.InputGroupText(html.I(className="bi bi-search")),
                                            dbc.Input(id="user-search", placeholder="Search email or role...", type="text"),
                                        ],
                                        size="sm",
                                    ),
                                    md=4,
                                ),
                                dbc.Col(
                                    dbc.Button(
                                        [html.I(className="bi bi-arrow-clockwise me-2"), "Refresh"],
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
                                            dbc.Button("Enable", id="btn-enable", color="success", size="sm"),
                                            dbc.Button("Disable", id="btn-disable", color="warning", size="sm"),
                                            dbc.Button("Delete", id="btn-delete", color="danger", size="sm"),
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
                                            [dbc.Select(id="assign-role-select", options=[], placeholder="Choose role"),
                                             dbc.Button("Assign", id="assign-role-btn", color="primary")],
                                            className="mb-2",
                                        ),
                                    ],
                                    md=5,
                                ),
                            ]
                        ),
                        dbc.Alert(id="user-action-alert", is_open=False, dismissable=True, className="mb-3"),
                        dash_table.DataTable(
                            id="users-table",
                            columns=[
                                {"name": "ID", "id": "id", "type": "numeric"},
                                {"name": "Email", "id": "email", "type": "text"},
                                {"name": "Role", "id": "role", "type": "text"},
                                {"name": "Status", "id": "status", "type": "text"},
                                {"name": "Created At", "id": "created_at", "type": "text"},
                                {"name": "Created By", "id": "created_by", "type": "text"},
                            ],
                            data=[],
                            row_selectable="single",
                            sort_action="native",
                            filter_action="native",
                            page_action="native",
                            page_size=10,
                            style_cell={"textAlign": "left", "padding": "10px", "whiteSpace": "normal", "height": "auto"},
                            style_data_conditional=[
                                {"if": {"column_id": "role", "filter_query": '{role} = "admin"'}, "backgroundColor": "#fff3cd", "fontWeight": "bold"},
                                {"if": {"column_id": "status", "filter_query": '{status} = "Inactive"'}, "backgroundColor": "#f8d7da", "color": "#721c24"},
                                {"if": {"column_id": "status", "filter_query": '{status} = "Active"'}, "backgroundColor": "#d4edda", "color": "#155724"},
                            ],
                            style_header={"backgroundColor": "rgb(230,230,230)", "fontWeight": "bold"},
                        ),
                        dbc.Modal(
                            [
                                dbc.ModalHeader("Confirm Action"),
                                dbc.ModalBody(id="confirm-modal-body"),
                                dbc.ModalFooter(
                                    [dbc.Button("Cancel", id="cancel-action-btn", color="secondary"),
                                     dbc.Button("Confirm", id="confirm-action-btn", color="danger")]
                                ),
                            ],
                            id="confirm-modal",
                            is_open=False,
                        ),
                    ]
                ),
            ]
        ),
        dcc.Store(id="pending-action-store"),
        dcc.Store(id="rbac-refresh"),
        dcc.Interval(id="users-interval", interval=30_000),
    ],
    fluid=True,
    className="p-4",
)

# ==================== STATISTICS CALLBACKS ====================
@app.callback(
    [Output("total-users-count", "children"),
     Output("active-users-count", "children"),
     Output("admin-users-count", "children"),
     Output("recent-logins-count", "children")],
    [Input("users-interval", "n_intervals")],
    prevent_initial_call=False,
)
def update_statistics(_):
    try:
        with session_scope(False) as db_session:
            all_users = user_service.get_all_users(db_session)
            total_users = len(all_users)

            admin_users = 0
            for u in all_users:
                rn = (_role_name(u, db_session) or "").lower()
                if rn == "admin":
                    admin_users += 1

            active_users = sum(
                                1
                                for u in all_users
                                if len(session_service.get_active_sessions(_get_attr(u, "id"), db_session)) > 0
                                )
            from datetime import datetime, timedelta
            cutoff = datetime.now() - timedelta(hours=24)
            from schemas.database_models import Session as DBSession
            recent_logins = 0
            for u in all_users:
                count_24h = (
                    db_session.query(DBSession)
                    .filter(DBSession.user_id == _get_attr(u, "id"))
                    .filter(DBSession.created_at >= cutoff)
                    .count()
                )
                if count_24h > 0:
                    recent_logins += 1

        return total_users, active_users, admin_users, recent_logins
    except Exception as e:
        logging.error(f"Error updating statistics: {e}")
        return "0", "0", "0", "0"

# ==================== USER CREATION CALLBACK ====================
@app.callback(
    [Output("create-user-alert", "children"),
     Output("create-user-alert", "is_open"),
     Output("create-user-alert", "color"),
     Output("new-user-email", "value"),
     Output("new-user-password", "value"),
     Output("rbac-refresh", "data")],
    [Input("create-user-btn", "n_clicks")],
    [State("new-user-email", "value"),
     State("new-user-password", "value"),
     State("new-user-role", "value")],
    prevent_initial_call=True,
)
def create_user(n_clicks, email, password, role_name):
    if not n_clicks:
        raise PreventUpdate
    if not all([email, password, role_name]):
        return "Please fill all fields", True, "danger", dash.no_update, dash.no_update, dash.no_update
    if len(password) < 8:
        return "Password must be at least 8 characters", True, "danger", dash.no_update, dash.no_update, dash.no_update

    try:
        with session_scope() as db_session:
            existing = user_service.get_user_by_email(email, db_session)
            if existing:
                return f"User {email} already exists", True, "warning", dash.no_update, dash.no_update, dash.no_update

            role = role_service.get_role_by_name(role_name, db_session)
            if not role:
                return f"Role {role_name} not found", True, "danger", dash.no_update, dash.no_update, dash.no_update

            salt = bcrypt.gensalt()
            hashed = bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

            new_user = user_service.create_user(
                email=email,
                password=hashed,
                role_id=role.id,
                session=db_session,
                created_by=None,  # TODO: current user id
            )

            if new_user:
                return f"User {email} created successfully", True, "success", "", "", {"refresh": True}
            else:
                return "Failed to create user", True, "danger", dash.no_update, dash.no_update, dash.no_update
    except Exception as e:
        logging.error(f"Error creating user: {e}")
        return f"Error: {str(e)}", True, "danger", dash.no_update, dash.no_update, dash.no_update

# ==================== ROLE MANAGEMENT CALLBACKS ====================
@app.callback(
    [Output("new-user-role", "options"),
     Output("edit-role-select", "options"),
     Output("assign-role-select", "options")],
    [Input("rbac-refresh", "data")],
    prevent_initial_call=False,
)
def update_role_dropdowns(_):
    try:
        with session_scope(False) as db_session:
            from schemas.database_models import Role
            roles = db_session.query(Role).all()
            role_options = [{"label": r.role_name, "value": r.role_name} for r in roles]
        return role_options, role_options, role_options
    except Exception as e:
        logging.error(f"Error loading roles: {e}")
        return [], [], []

@app.callback(
    [Output("roles-alert", "children"),
     Output("roles-alert", "is_open"),
     Output("roles-alert", "color"),
     Output("new-role-name", "value"),
     Output("perm-pages-checklist", "value"),
     Output("rbac-refresh", "data", allow_duplicate=True)],
    [Input("create-role-btn", "n_clicks")],
    [State("new-role-name", "value"),
     State("perm-pages-checklist", "value")],
    prevent_initial_call=True,
)
def create_role_with_permissions(n_clicks, role_name, selected_pages):
    if not n_clicks:
        raise PreventUpdate
    if not role_name:
        return "Please enter a role name", True, "danger", dash.no_update, dash.no_update, dash.no_update

    try:
        with session_scope() as db_session:
            existing = role_service.get_role_by_name(role_name, db_session)
            if existing:
                return f"Role {role_name} already exists", True, "warning", dash.no_update, dash.no_update, dash.no_update

            new_role = role_service.create_role(
                role_name=role_name,
                session=db_session,
                created_by=None,  # TODO: current user id
            )

            if selected_pages:
                pages_to_assign = []
                for page_name in selected_pages:
                    page = page_service.get_page_by_name(page_name, db_session)
                    if not page:
                        page = page_service.create_page(page_name, db_session)
                    pages_to_assign.append(page)
                role_service.assign_pages_to_role(new_role, pages_to_assign, db_session)

            return f"Role {role_name} created with {len(selected_pages or [])} permissions", True, "success", "", [], {"refresh": True}
    except Exception as e:
        logging.error(f"Error creating role: {e}")
        return f"Error: {str(e)}", True, "danger", dash.no_update, dash.no_update, dash.no_update

# ==================== EDIT ROLE CALLBACKS ====================
@app.callback(
    [Output("edit-perm-pages-checklist", "value"),
     Output("edit-pages-count", "children")],
    [Input("edit-role-select", "value")],
    prevent_initial_call=True,
)
def load_role_permissions(role_name):
    if not role_name:
        return [], "0"
    try:
        with session_scope(False) as db_session:
            role = role_service.get_role_by_name(role_name, db_session)
            if role:
                selected_pages = [p.page_name for p in role.pages]
                return selected_pages, str(len(selected_pages))
        return [], "0"
    except Exception as e:
        logging.error(f"Error loading role permissions: {e}")
        return [], "0"

@app.callback(
    [Output("edit-roles-alert", "children"),
     Output("edit-roles-alert", "is_open"),
     Output("edit-roles-alert", "color"),
     Output("rbac-refresh", "data", allow_duplicate=True)],
    [Input("update-perms-btn", "n_clicks")],
    [State("edit-role-select", "value"),
     State("edit-perm-pages-checklist", "value")],
    prevent_initial_call=True,
)
def update_role_permissions(n_clicks, role_name, selected_pages):
    if not n_clicks or not role_name:
        raise PreventUpdate
    try:
        with session_scope() as db_session:
            role = role_service.get_role_by_name(role_name, db_session)
            if not role:
                return f"Role {role_name} not found", True, "danger", dash.no_update

            role.pages.clear()

            if selected_pages:
                pages_to_assign = []
                for page_name in selected_pages:
                    page = page_service.get_page_by_name(page_name, db_session)
                    if not page:
                        page = page_service.create_page(page_name, db_session)
                    pages_to_assign.append(page)
                role_service.assign_pages_to_role(role, pages_to_assign, db_session)

            return f"Updated {role_name} with {len(selected_pages or [])} permissions", True, "success", {"refresh": True}
    except Exception as e:
        logging.error(f"Error updating role: {e}")
        return f"Error: {str(e)}", True, "danger", dash.no_update

@app.callback(
    [Output("edit-roles-alert", "children", allow_duplicate=True),
     Output("edit-roles-alert", "is_open", allow_duplicate=True),
     Output("edit-roles-alert", "color", allow_duplicate=True),
     Output("edit-role-select", "value"),
     Output("rbac-refresh", "data", allow_duplicate=True)],
    [Input("edit-delete-role-btn", "n_clicks")],
    [State("edit-role-select", "value")],
    prevent_initial_call=True,
)
def delete_role(n_clicks, role_name):
    if not n_clicks or not role_name:
        raise PreventUpdate
    if role_name == "admin":
        return "Cannot delete admin role", True, "warning", dash.no_update, dash.no_update
    try:
        with session_scope() as db_session:
            role = role_service.get_role_by_name(role_name, db_session)
            if not role:
                return f"Role {role_name} not found", True, "danger", dash.no_update, dash.no_update
            if getattr(role, "users", None):
                return f"Cannot delete role with {len(role.users)} users", True, "warning", dash.no_update, dash.no_update

            success = role_service.delete_role(role.id, 0, db_session)
            if success:
                return f"Role {role_name} deleted", True, "success", None, {"refresh": True}
            else:
                return "Failed to delete role", True, "danger", dash.no_update, dash.no_update
    except Exception as e:
        logging.error(f"Error deleting role: {e}")
        return f"Error: {str(e)}", True, "danger", dash.no_update, dash.no_update

# ==================== USER TABLE CALLBACKS ====================
@app.callback(
    Output("users-table", "data"),
    [Input("users-interval", "n_intervals"),
     Input("rbac-refresh", "data"),
     Input("user-search", "value")],
    prevent_initial_call=False,
)
def update_users_table(_, __, search_term):
    try:
        with session_scope(False) as db_session:
            users = user_service.get_all_users(db_session)
            table_data = []
            for u in users:
                row = {
                    "id": _get_attr(u, "id"),
                    "email": _get_attr(u, "email", default=""),
                    "role": _role_name(u, db_session) or "No Role",
                    "status": "Inactive" if _is_disabled(u) else "Active",
                    "created_at": _created_at_str(u),
                    "created_by": _creator_email(u, db_session),
                }
                if search_term:
                    q = (search_term or "").lower()
                    if q in row["email"].lower() or q in row["role"].lower():
                        table_data.append(row)
                else:
                    table_data.append(row)
        return table_data
    except Exception as e:
        logging.error(f"Error updating users table: {e}")
        return []

# ==================== USER ACTIONS CALLBACKS ====================
@app.callback(
    [Output("confirm-modal", "is_open"),
     Output("confirm-modal-body", "children"),
     Output("pending-action-store", "data")],
    [Input("btn-enable", "n_clicks"),
     Input("btn-disable", "n_clicks"),
     Input("btn-delete", "n_clicks")],
    [State("users-table", "selected_rows"), State("users-table", "data")],
    prevent_initial_call=True,
)
def show_confirm_modal(enable_clicks, disable_clicks, delete_clicks, selected_rows, table_data):
    if not selected_rows or not table_data:
        raise PreventUpdate
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    selected_user = table_data[selected_rows[0]]

    if button_id == "btn-enable":
        message, action = f"Enable user {selected_user['email']}?", "enable"
    elif button_id == "btn-disable":
        message, action = f"Disable user {selected_user['email']}?", "disable"
    elif button_id == "btn-delete":
        message, action = f"Delete user {selected_user['email']}? This action cannot be undone.", "delete"
    else:
        raise PreventUpdate

    return True, message, {"action": action, "user_id": selected_user["id"]}

@app.callback(
    [Output("user-action-alert", "children"),
     Output("user-action-alert", "is_open"),
     Output("user-action-alert", "color"),
     Output("confirm-modal", "is_open", allow_duplicate=True),
     Output("rbac-refresh", "data", allow_duplicate=True)],
    [Input("confirm-action-btn", "n_clicks")],
    [State("pending-action-store", "data")],
    prevent_initial_call=True,
)
def execute_user_action(n_clicks, pending_action):
    if not n_clicks or not pending_action:
        raise PreventUpdate
    action = pending_action["action"]
    user_id = pending_action["user_id"]

    try:
        with session_scope() as db_session:
            if action == "enable":
                user = user_service.update_user(user_id, db_session, disabled=False)
                if user:
                    return "User enabled", True, "success", False, {"refresh": True}
            elif action == "disable":
                user = user_service.update_user(user_id, db_session, disabled=True)
                if user:
                    user_obj = user_service.get_user_by_id(user_id, db_session)
                    if user_obj:
                        try:
                            # Prefer the service if it exposes a delete/revoke for a user
                            # (try common names to avoid editing the service right now)
                            for fn_name in (
                                "delete_sessions_for_user",
                                "revoke_user_sessions",
                                "revoke_sessions_for_user",
                                "delete_user_sessions",
                            ):
                                fn = getattr(session_service, fn_name, None)
                                if fn:
                                    fn(_get_attr(user_obj, "id"), db_session)
                                    break
                            else:
                                # Fallback: delete directly in DB by user_id
                                from schemas.database_models import Session as DBSession
                                db_session.query(DBSession).filter(
                                    DBSession.user_id == _get_attr(user_obj, "id")
                                ).delete(synchronize_session=False)
                        except Exception:
                            # Non-fatal for UI; we still disabled the account
                            pass
                    return "User disabled", True, "warning", False, {"refresh": True}
            elif action == "delete":
                success = user_service.delete_user(user_id, db_session)
                if success:
                    return "User deleted", True, "success", False, {"refresh": True}
        return "Action failed", True, "danger", False, dash.no_update
    except Exception as e:
        logging.error(f"Error executing user action: {e}")
        return f"Error: {str(e)}", True, "danger", False, dash.no_update

@app.callback(
    [Output("user-action-alert", "children", allow_duplicate=True),
     Output("user-action-alert", "is_open", allow_duplicate=True),
     Output("user-action-alert", "color", allow_duplicate=True),
     Output("rbac-refresh", "data", allow_duplicate=True)],
    [Input("assign-role-btn", "n_clicks")],
    [State("assign-role-select", "value"),
     State("users-table", "selected_rows"),
     State("users-table", "data")],
    prevent_initial_call=True,
)
def assign_role_to_user(n_clicks, role_name, selected_rows, table_data):
    if not n_clicks or not role_name or not selected_rows:
        raise PreventUpdate
    selected_user = table_data[selected_rows[0]]
    try:
        with session_scope() as db_session:
            role = role_service.get_role_by_name(role_name, db_session)
            if not role:
                return f"Role {role_name} not found", True, "danger", dash.no_update
            user = user_service.update_user(selected_user["id"], db_session, role_id=role.id)
            if user:
                return f"Assigned {role_name} to {selected_user['email']}", True, "success", {"refresh": True}
            else:
                return "Failed to assign role", True, "danger", dash.no_update
    except Exception as e:
        logging.error(f"Error assigning role: {e}")
        return f"Error: {str(e)}", True, "danger", dash.no_update

# ==================== MODAL CLOSE CALLBACK ====================
@app.callback(
    Output("confirm-modal", "is_open", allow_duplicate=True),
    [Input("cancel-action-btn", "n_clicks")],
    prevent_initial_call=True,
)
def close_modal(n_clicks):
    if n_clicks:
        return False
    raise PreventUpdate
