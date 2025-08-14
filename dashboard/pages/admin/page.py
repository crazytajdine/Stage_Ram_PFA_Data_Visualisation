# dashboard/pages/admin/page.py
from dash import html, dcc, Input, Output, State, callback, dash_table, no_update
import dash_bootstrap_components as dbc
from server_instance import get_app
from dashboard.state import session_manager
import dash
from dash import Input, Output, State, html, dcc, dash_table
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
from dash.exceptions import PreventUpdate

from data_managers.database_manager import session_scope
from data_managers.session_manager import SessionManager
from services import user_service, role_service, page_service, session_service
from configurations.nav_config import NAV_CONFIG
from server_instance import get_app

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
    meta = []
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
        # Roles & Permissions — one-click create (role + permissions)
        dbc.Card(
            [
                dbc.CardHeader(
                    html.H4("Create Role with Permissions", className="mb-0")
                ),
                dbc.CardBody(
                    [
                        # Role name
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        dbc.Label("Role name"),
                                        dbc.Input(
                                            id="new-role-name",
                                            placeholder="e.g., perf, ops, finance",
                                        ),
                                    ],
                                    md=6,
                                ),
                            ],
                            className="g-3 mb-3",
                        ),
                        # Permissions (all pages from navbar)
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        dbc.Label("Allowed pages"),
                                        dcc.Checklist(
                                            id="perm-pages-checklist",
                                            options=_all_page_options(),  # ← pull from navbar
                                            value=[],  # nothing preselected
                                            labelStyle={"display": "block"},
                                            inputStyle={"marginRight": "8px"},
                                        ),
                                    ],
                                    md=8,
                                ),
                            ],
                            className="g-3",
                        ),
                        # Bottom actions
                        html.Div(
                            dbc.Button(
                                [
                                    html.I(className="bi bi-shield-plus me-2"),
                                    "Create Role",
                                ],
                                id="create-role-btn",
                                color="primary",
                                className="w-100 mt-3",
                            ),
                            className="d-flex justify-content-end",
                        ),
                        # Feedback
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
        # ─────────────────────────────────────────────
        # ✏️ Edit Role & Permissions — dropdown + pages list + footer actions
        dbc.Card(
            [
                dbc.CardHeader(html.H4("Edit Role & Permissions", className="mb-0")),
                dbc.CardBody(
                    [
                        # Pick the role to edit
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        dbc.Label("Select role"),
                                        dbc.Select(
                                            id="edit-role-select",
                                            options=[],  # ← fill from your roles source/callback
                                            placeholder="Choose a role",
                                        ),
                                        dbc.FormText(
                                            "Pick a role to view and modify its allowed pages."
                                        ),
                                    ],
                                    md=6,
                                ),
                            ],
                            className="g-3 mb-3",
                        ),
                        # Pages checklist (from navbar)
                        dbc.Label("Allowed pages"),
                        html.Div(
                            dcc.Checklist(
                                id="edit-perm-pages-checklist",
                                options=_all_page_options(),  # ← uses your navbar helper
                                value=[],  # ← fill with current role's pages
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
                        # Tiny status line
                        html.Small(
                            [
                                "Selected ",
                                html.Span("0", id="edit-pages-count"),
                                " page(s)",
                            ],
                            className="text-muted",
                        ),
                        # Feedback
                        dbc.Alert(
                            id="edit-roles-alert",
                            is_open=False,
                            dismissable=True,
                            className="mt-3",
                        ),
                    ]
                ),
                # Edge-to-edge footer with Update & Delete
                dbc.CardFooter(
                    dbc.Row(
                        [
                            dbc.Col(
                                dbc.Button(
                                    [
                                        html.I(className="bi bi-save2 me-2"),
                                        "Update Permissions",
                                    ],
                                    id="update-perms-btn",
                                    color="dark",
                                    className="w-100 rounded-0 py-3 text-uppercase fw-semibold",
                                ),
                                className="p-0",
                            ),
                            dbc.Col(
                                dbc.Button(
                                    [
                                        html.I(className="bi bi-trash me-2"),
                                        "Delete Role",
                                    ],
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
# admin_callbacks.py

# ==================== STATISTICS CALLBACKS ====================

@app.callback(
    [
        Output("total-users-count", "children"),
        Output("active-users-count", "children"),
        Output("admin-users-count", "children"),
        Output("recent-logins-count", "children"),
    ],
    [Input("users-interval", "n_intervals")],
    prevent_initial_call=False,
)
def update_statistics(_):
    try:
        with session_scope(False) as db_session:
            all_users = user_service.get_all_users(db_session)
            total_users = len(all_users)

            # Robust admin count regardless of DTO shape
            admin_users = 0
            for u in all_users:
                rn = (_role_name(u, db_session) or "").lower()
                if rn == "admin":
                    admin_users += 1

            # Active sessions (your existing logic)
            session_counts = session_manager.get_active_sessions_count()
            active_users = session_counts.get("total", 0)

            # "Recent logins" (keeps your current approach)
            recent_logins = 0
            for u in all_users:
                sessions = session_service.get_active_sessions(_get_attr(u, "id"), db_session)
                if sessions:
                    recent_logins += 1

        return total_users, active_users, admin_users, recent_logins
    except Exception as e:
        logging.error(f"Error updating statistics: {e}")
        return "0", "0", "0", "0"

# ==================== USER CREATION CALLBACK ====================

@app.callback(
    [
        Output("create-user-alert", "children"),
        Output("create-user-alert", "is_open"),
        Output("create-user-alert", "color"),
        Output("new-user-email", "value"),
        Output("new-user-password", "value"),
        Output("rbac-refresh", "data"),
    ],
    [Input("create-user-btn", "n_clicks")],
    [
        State("new-user-email", "value"),
        State("new-user-password", "value"),
        State("new-user-role", "value"),
    ],
    prevent_initial_call=True,
)
def create_user(n_clicks, email, password, role_name):
    """Create new user using existing user_service"""
    if not n_clicks:
        raise PreventUpdate
        
    if not all([email, password, role_name]):
        return "Please fill all fields", True, "danger", dash.no_update, dash.no_update, dash.no_update
        
    if len(password) < 8:
        return "Password must be at least 8 characters", True, "danger", dash.no_update, dash.no_update, dash.no_update
        
    try:
        with session_scope() as db_session:
            # Check if user exists using existing service
            existing = user_service.get_user_by_email(email, db_session)
            if existing:
                return f"User {email} already exists", True, "warning", dash.no_update, dash.no_update, dash.no_update
            
            # Get role using existing service
            role = role_service.get_role_by_name(role_name, db_session)
            if not role:
                return f"Role {role_name} not found", True, "danger", dash.no_update, dash.no_update, dash.no_update
            
            # Hash password using bcrypt (matching your existing pattern)
            salt = bcrypt.gensalt()
            hashed = bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")
            
            # Create user using existing service
            new_user = user_service.create_user(
                email=email,
                password=hashed,
                role_id=role.id,
                session=db_session,
                created_by=None  # TODO: Get from current session
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
    [
        Output("new-user-role", "options"),
        Output("edit-role-select", "options"),
        Output("assign-role-select", "options"),
    ],
    [Input("rbac-refresh", "data")],
    prevent_initial_call=False,
)
def update_role_dropdowns(_):
    """Populate role dropdowns using existing services"""
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
    [
        Output("roles-alert", "children"),
        Output("roles-alert", "is_open"),
        Output("roles-alert", "color"),
        Output("new-role-name", "value"),
        Output("perm-pages-checklist", "value"),
        Output("rbac-refresh", "data", allow_duplicate=True),
    ],
    [Input("create-role-btn", "n_clicks")],
    [
        State("new-role-name", "value"),
        State("perm-pages-checklist", "value"),
    ],
    prevent_initial_call=True,
)
def create_role_with_permissions(n_clicks, role_name, selected_pages):
    """Create role with permissions using existing services"""
    if not n_clicks:
        raise PreventUpdate
        
    if not role_name:
        return "Please enter a role name", True, "danger", dash.no_update, dash.no_update, dash.no_update
        
    try:
        with session_scope() as db_session:
            # Check if role exists
            existing = role_service.get_role_by_name(role_name, db_session)
            if existing:
                return f"Role {role_name} already exists", True, "warning", dash.no_update, dash.no_update, dash.no_update
            
            # Create role using existing service
            new_role = role_service.create_role(
                role_name=role_name,
                session=db_session,
                created_by=None  # TODO: Get from current session
            )
            
            # Assign pages if selected
            if selected_pages:
                pages_to_assign = []
                for page_name in selected_pages:
                    page = page_service.get_page_by_name(page_name, db_session)
                    if not page:
                        # Create page if it doesn't exist
                        page = page_service.create_page(page_name, db_session)
                    pages_to_assign.append(page)
                
                role_service.assign_pages_to_role(new_role, pages_to_assign, db_session)
            
            return f"Role {role_name} created with {len(selected_pages or [])} permissions", True, "success", "", [], {"refresh": True}
            
    except Exception as e:
        logging.error(f"Error creating role: {e}")
        return f"Error: {str(e)}", True, "danger", dash.no_update, dash.no_update, dash.no_update

# ==================== EDIT ROLE CALLBACKS ====================

@app.callback(
    [
        Output("edit-perm-pages-checklist", "value"),
        Output("edit-pages-count", "children"),
    ],
    [Input("edit-role-select", "value")],
    prevent_initial_call=True,
)
def load_role_permissions(role_name):
    """Load current permissions for selected role"""
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
    [
        Output("edit-roles-alert", "children"),
        Output("edit-roles-alert", "is_open"),
        Output("edit-roles-alert", "color"),
        Output("rbac-refresh", "data", allow_duplicate=True),
    ],
    [Input("update-perms-btn", "n_clicks")],
    [
        State("edit-role-select", "value"),
        State("edit-perm-pages-checklist", "value"),
    ],
    prevent_initial_call=True,
)
def update_role_permissions(n_clicks, role_name, selected_pages):
    """Update role permissions using existing services"""
    if not n_clicks or not role_name:
        raise PreventUpdate
        
    try:
        with session_scope() as db_session:
            role = role_service.get_role_by_name(role_name, db_session)
            if not role:
                return f"Role {role_name} not found", True, "danger", dash.no_update
            
            # Clear existing pages
            role.pages.clear()
            
            # Assign new pages
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
    [
        Output("edit-roles-alert", "children", allow_duplicate=True),
        Output("edit-roles-alert", "is_open", allow_duplicate=True),
        Output("edit-roles-alert", "color", allow_duplicate=True),
        Output("edit-role-select", "value"),
        Output("rbac-refresh", "data", allow_duplicate=True),
    ],
    [Input("edit-delete-role-btn", "n_clicks")],
    [State("edit-role-select", "value")],
    prevent_initial_call=True,
)
def delete_role(n_clicks, role_name):
    """Delete role using existing service"""
    if not n_clicks or not role_name:
        raise PreventUpdate
        
    if role_name == "admin":
        return "Cannot delete admin role", True, "warning", dash.no_update, dash.no_update
        
    try:
        with session_scope() as db_session:
            role = role_service.get_role_by_name(role_name, db_session)
            if not role:
                return f"Role {role_name} not found", True, "danger", dash.no_update, dash.no_update
            
            # Check if role has users
            if role.users:
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
    [
        Input("users-interval", "n_intervals"),
        Input("rbac-refresh", "data"),
        Input("user-search", "value"),
    ],
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
                    q = search_term.lower()
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
    [
        Output("confirm-modal", "is_open"),
        Output("confirm-modal-body", "children"),
        Output("pending-action-store", "data"),
    ],
    [
        Input("btn-enable", "n_clicks"),
        Input("btn-disable", "n_clicks"),
        Input("btn-delete", "n_clicks"),
    ],
    [State("users-table", "selected_rows"), State("users-table", "data")],
    prevent_initial_call=True,
)
def show_confirm_modal(enable_clicks, disable_clicks, delete_clicks, selected_rows, table_data):
    """Show confirmation modal for user actions"""
    if not selected_rows or not table_data:
        raise PreventUpdate
        
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate
        
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    selected_user = table_data[selected_rows[0]]
    
    if button_id == "btn-enable":
        message = f"Enable user {selected_user['email']}?"
        action = "enable"
    elif button_id == "btn-disable":
        message = f"Disable user {selected_user['email']}?"
        action = "disable"
    elif button_id == "btn-delete":
        message = f"Delete user {selected_user['email']}? This action cannot be undone."
        action = "delete"
    else:
        raise PreventUpdate
        
    return True, message, {"action": action, "user_id": selected_user["id"]}

@app.callback(
    [
        Output("user-action-alert", "children"),
        Output("user-action-alert", "is_open"),
        Output("user-action-alert", "color"),
        Output("confirm-modal", "is_open", allow_duplicate=True),
        Output("rbac-refresh", "data", allow_duplicate=True),
    ],
    [Input("confirm-action-btn", "n_clicks")],
    [State("pending-action-store", "data")],
    prevent_initial_call=True,
)
def execute_user_action(n_clicks, pending_action):
    """Execute user action using existing services"""
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
                    # Also delete their sessions
                    user_obj = user_service.get_user_by_id(user_id, db_session)
                    if user_obj:
                        session_manager.delete_user_sessions(user_obj.email)
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
    [
        Output("user-action-alert", "children", allow_duplicate=True),
        Output("user-action-alert", "is_open", allow_duplicate=True),
        Output("user-action-alert", "color", allow_duplicate=True),
        Output("rbac-refresh", "data", allow_duplicate=True),
    ],
    [Input("assign-role-btn", "n_clicks")],
    [
        State("assign-role-select", "value"),
        State("users-table", "selected_rows"),
        State("users-table", "data"),
    ],
    prevent_initial_call=True,
)
def assign_role_to_user(n_clicks, role_name, selected_rows, table_data):
    """Assign role to selected user"""
    if not n_clicks or not role_name or not selected_rows:
        raise PreventUpdate
        
    selected_user = table_data[selected_rows[0]]
    
    try:
        with session_scope() as db_session:
            role = role_service.get_role_by_name(role_name, db_session)
            if not role:
                return f"Role {role_name} not found", True, "danger", dash.no_update
                
            user = user_service.update_user(
                selected_user["id"], 
                db_session, 
                role_id=role.id
            )
            
            if user:
                return f"Assigned {role_name} to {selected_user['email']}", True, "success", {"refresh": True}
            else:
                return "Failed to assign role", True, "danger", dash.no_update
                
    except Exception as e:
        logging.error(f"Error assigning role: {e}")
        return f"Error: {str(e)}", True, "danger", dash.no_update

# ==================== LOGIN ACTIVITY CHART ====================

@app.callback(
    Output("login-activity-chart", "figure"),
    [Input("users-interval", "n_intervals")],
    prevent_initial_call=False,
)
def update_login_activity_chart(_):
    """Generate login activity chart"""
    try:
        # Generate sample data for last 7 days
        dates = [(datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(6, -1, -1)]
        
        with session_scope(False) as db_session:
            # Count sessions per day (simplified - you may want to aggregate from your session logs)
            from schemas.database_models import Session
            
            daily_counts = []
            for date_str in dates:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                next_day = date_obj + timedelta(days=1)
                
                count = db_session.query(Session).filter(
                    Session.created_at >= date_obj,
                    Session.created_at < next_day
                ).count()
                daily_counts.append(count)
        
        figure = go.Figure()
        figure.add_trace(go.Bar(
            x=dates,
            y=daily_counts,
            marker_color='rgb(55, 83, 109)',
            text=daily_counts,
            textposition='auto',
        ))
        
        figure.update_layout(
            title="Login Activity (Last 7 Days)",
            xaxis_title="Date",
            yaxis_title="Number of Logins",
            showlegend=False,
            hovermode='x unified',
            template='plotly_white',
            margin=dict(l=0, r=0, t=30, b=0),
            height=300,
        )
        
        return figure
        
    except Exception as e:
        logging.error(f"Error generating login chart: {e}")
        # Return empty chart on error
        return go.Figure().add_annotation(
            text="Unable to load data",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )

# ==================== MODAL CLOSE CALLBACK ====================

@app.callback(
    Output("confirm-modal", "is_open", allow_duplicate=True),
    [Input("cancel-action-btn", "n_clicks")],
    prevent_initial_call=True,
)
def close_modal(n_clicks):
    """Close confirmation modal"""
    if n_clicks:
        return False
    raise PreventUpdate
