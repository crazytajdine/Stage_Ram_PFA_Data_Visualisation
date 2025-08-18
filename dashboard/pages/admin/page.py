# dashboard/pages/admin/page.py
from __future__ import annotations

import logging
import dash
from dash import Input, Output, State, html, dcc, dash_table
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc

from dashboard.components.auth import add_state_user_id
from dashboard.utils_dashboard.utils_page import (
    get_all_metadata_id_pages_dynamic,
    get_all_metadata_pages_dynamic,
)
from server_instance import get_app
from data_managers.database_manager import session_scope

from services import user_service, role_service, page_service, session_service

app = get_app()

ID_CREATE_PAGES_CHECKLIST = "create-pages-checklist"
ID_CREATE_IS_ADMIN_CHECKBOX = "create-is-admin-pages-checkbox"
ID_CREATE_ALTER_FILE_CHECKBOX = "create-alter-file-pages-checkbox"

ID_EDIT_PAGES_CHECKLIST = "edit-pages-checklist"
ID_EDIT_IS_ADMIN_CHECKBOX = "edit-is-admin-pages-checkbox"
ID_EDIT_ALTER_FILE_CHECKBOX = "edit-alter-file-pages-checkbox"

ID_SELECT_ROLE = "edit-role-select"


def enable_user(user_id):
    with session_scope() as db_session:
        user = user_service.update_user(user_id, db_session, disabled=False)
        if user:
            return "User enabled", True, "success", False, {"refresh": True}
    return "Enable failed", True, "danger", False, {"refresh": False}


def disable_user(user_id):
    with session_scope() as db_session:
        user = user_service.update_user(user_id, db_session, disabled=True)
        if user:
            session_service.delete_session_with_user_id(user_id, db_session)

            return "User disabled", True, "warning", False, {"refresh": True}
    return "Disable failed", True, "danger", False, {"refresh": False}


def delete_user(user_id):
    with session_scope() as db_session:
        success = user_service.delete_user(user_id, db_session)
        if success:
            return "User deleted", True, "success", False, {"refresh": True}
    return "Delete failed", True, "danger", False, {"refresh": False}


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
                    md=4,
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
                    md=4,
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
                    md=4,
                ),
            ],
            className="mb-4",
        ),
        # Create Role with permissions
        dbc.Card(
            [
                dbc.CardHeader(
                    html.H4("Create Role with permissions", className="mb-0")
                ),
                dbc.CardBody(
                    [
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
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        dbc.Label("Permissions"),
                                        html.Div(
                                            children=[
                                                dbc.Checkbox(
                                                    id=ID_CREATE_IS_ADMIN_CHECKBOX,
                                                    label="Is Admin",
                                                ),
                                                dbc.Checkbox(
                                                    id=ID_CREATE_ALTER_FILE_CHECKBOX,
                                                    label="Alter File",
                                                ),
                                            ],
                                            style={
                                                "border": "1px solid #e9ecef",
                                                "borderRadius": "0.5rem",
                                                "padding": "12px",
                                                "background": "#fff",
                                            },
                                        ),
                                    ],
                                    md=6,
                                    className="mb-2",
                                ),
                            ]
                        ),
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        dbc.Label("Allowed pages"),
                                        dcc.Checklist(
                                            id=ID_CREATE_PAGES_CHECKLIST,
                                            labelStyle={"display": "block"},
                                            inputStyle={"marginRight": "8px"},
                                            style={
                                                "overflowY": "auto",
                                                "border": "1px solid #e9ecef",
                                                "borderRadius": "0.5rem",
                                                "padding": "12px",
                                                "background": "#fff",
                                            },
                                        ),
                                    ],
                                    md=8,
                                ),
                            ],
                            className="g-3",
                        ),
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
        # Edit Role & pages
        dbc.Card(
            [
                dbc.CardHeader(html.H4("Edit Role & pages", className="mb-0")),
                dbc.CardBody(
                    [
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        dbc.Label("Select role"),
                                        dbc.Select(
                                            id=ID_SELECT_ROLE,
                                            options=[],
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
                        dbc.Alert(
                            id="edit-roles-alert",
                            is_open=False,
                            dismissable=True,
                            className="mt-3",
                        ),
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        dbc.Label("Permissions"),
                                        html.Div(
                                            children=[
                                                dbc.Checkbox(
                                                    id=ID_EDIT_IS_ADMIN_CHECKBOX,
                                                    label="Is Admin",
                                                ),
                                                dbc.Checkbox(
                                                    id=ID_EDIT_ALTER_FILE_CHECKBOX,
                                                    label="Alter File",
                                                ),
                                            ],
                                            style={
                                                "border": "1px solid #e9ecef",
                                                "borderRadius": "0.5rem",
                                                "padding": "12px",
                                                "background": "#fff",
                                            },
                                        ),
                                    ],
                                    md=6,
                                    className="mb-2",
                                ),
                            ]
                        ),
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        dbc.Label("Allowed pages"),
                                        html.Div(
                                            dcc.Checklist(
                                                id=ID_EDIT_PAGES_CHECKLIST,
                                                labelStyle={"display": "block"},
                                                inputStyle={"marginRight": "8px"},
                                            ),
                                            style={
                                                "border": "1px solid #e9ecef",
                                                "borderRadius": "0.5rem",
                                                "padding": "12px",
                                                "background": "#fff",
                                            },
                                        ),
                                        html.Small(
                                            [
                                                "Selected ",
                                                html.Span("0", id="edit-pages-count"),
                                                " page(s)",
                                            ],
                                            className="text-muted",
                                        ),
                                    ],
                                    md=6,
                                ),
                            ]
                        ),
                    ]
                ),
                dbc.CardFooter(
                    dbc.Row(
                        [
                            dbc.Col(
                                dbc.Button(
                                    [
                                        html.I(className="bi bi-save2 me-2"),
                                        "Update pages",
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
        # Users table + actions + assign role
        dbc.Card(
            [
                dbc.CardHeader(
                    dbc.Row(
                        [
                            dbc.Col(
                                html.H4("User Management", className="mb-0"),
                                md=4,
                            ),
                            dbc.Col(
                                dbc.Row(
                                    [
                                        # Enable / Disable group
                                        dbc.Col(
                                            dbc.ButtonGroup(
                                                [
                                                    dbc.Button(
                                                        "Enable",
                                                        id="btn-enable",
                                                        color="success",
                                                        size="sm",
                                                        className="rounded-start",
                                                    ),
                                                    dbc.Button(
                                                        "Disable",
                                                        id="btn-disable",
                                                        color="warning",
                                                        size="sm",
                                                        className="rounded-end",
                                                    ),
                                                ],
                                                className="me-2",
                                            ),
                                            width="auto",
                                        ),
                                        # Delete button
                                        dbc.Col(
                                            dbc.Button(
                                                "Delete",
                                                id="btn-delete",
                                                color="danger",
                                                size="sm",
                                                className="rounded-4 me-2",
                                            ),
                                            width="auto",
                                        ),
                                        # Refresh button
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
                                                outline=True,
                                                size="sm",
                                                className="rounded-4",
                                            ),
                                            width="auto",
                                        ),
                                    ],
                                    className="justify-content-end",
                                    align="center",
                                ),
                                md=8,
                            ),
                        ],
                        className="align-items-center",
                    )
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
                                {
                                    "name": "Email",
                                    "id": "email",
                                    "type": "text",
                                },
                                {"name": "Role id", "id": "role_id", "type": "text"},
                                {"name": "Role", "id": "role", "type": "text"},
                                {"name": "disabled", "id": "disabled", "type": "text"},
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
                            centered=True,
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
    [
        Output("total-users-count", "children"),
        Output("admin-users-count", "children"),
        Output("recent-logins-count", "children"),
    ],
    [Input("users-interval", "n_intervals")],
    prevent_initial_call=False,
)
def update_statistics(_):
    with session_scope(False) as db_session:
        all_users = user_service.get_all_users(db_session)
        total_users = len(all_users)

        admin_users = 0
        for u in all_users:
            if u.role_id == 0:
                admin_users += 1

        recent_logins = len(session_service.get_recent_logins(db_session))

    return total_users, admin_users, recent_logins


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
        add_state_user_id(),
    ],
    prevent_initial_call=True,
)
def create_user(n_clicks, email, password, role_id, user_id):
    if not n_clicks or user_id is None:
        raise PreventUpdate
    if not all([email, password, role_id is not None]):
        return (
            "Please fill all fields",
            True,
            "danger",
            dash.no_update,
            dash.no_update,
            dash.no_update,
        )
    if len(password) < 8:
        return (
            "Password must be at least 8 characters",
            True,
            "danger",
            dash.no_update,
            dash.no_update,
            dash.no_update,
        )

    with session_scope() as db_session:
        existing = user_service.get_user_by_email(email, db_session)
        if existing:
            return (
                f"User {email} already exists",
                True,
                "warning",
                dash.no_update,
                dash.no_update,
                dash.no_update,
            )

        role = role_service.get_role_by_id(role_id, db_session)
        if not role:
            return (
                f"Role {role_id} not found",
                True,
                "danger",
                dash.no_update,
                dash.no_update,
                dash.no_update,
            )

        hashed = user_service.hash_password(password)

        new_user = user_service.create_user(
            email=email,
            password=hashed,
            role_id=role.id,
            session=db_session,
            created_by=user_id,
        )

        if new_user:
            return (
                f"User {email} created successfully",
                True,
                "success",
                "",
                "",
                {"refresh": True},
            )
        else:
            return (
                "Failed to create user",
                True,
                "danger",
                dash.no_update,
                dash.no_update,
                dash.no_update,
            )


# ==================== ROLE MANAGEMENT CALLBACKS ====================


@app.callback(
    Output(ID_CREATE_PAGES_CHECKLIST, "options"),
    Input(ID_CREATE_IS_ADMIN_CHECKBOX, "value"),
)
def add_pages_to_create_checklist_options(is_admin) -> list[dict]:

    pages = get_all_metadata_pages_dynamic()
    pages.sort(key=lambda page: page.admin_page)

    opts = []
    for p in pages:
        if not is_admin and p.admin_page:
            continue

        pid = p.id

        if pid is None:
            continue
        label = p.name + f" (href: {p.href})"
        opts.append({"label": label, "value": pid})

    return opts


@app.callback(
    Output(ID_EDIT_PAGES_CHECKLIST, "options"),
    Input(ID_EDIT_IS_ADMIN_CHECKBOX, "value"),
)
def add_pages_to_edit_checklist_options(is_admin) -> list[dict]:

    pages = get_all_metadata_pages_dynamic()
    pages.sort(key=lambda page: page.admin_page)

    opts = []
    for p in pages:
        if not is_admin and p.admin_page:
            continue

        pid = p.id

        if pid is None:
            continue
        label = p.name + f" (href: {p.href})"
        opts.append({"label": label, "value": pid})

    return opts


@app.callback(
    [
        Output("new-user-role", "options"),
        Output(ID_SELECT_ROLE, "options"),
        Output("assign-role-select", "options"),
    ],
    [Input("rbac-refresh", "data")],
    prevent_initial_call=False,
)
def update_role_dropdowns(_):
    try:
        with session_scope(False) as session:

            roles = role_service.get_roles(session)
            role_options = [{"label": r.role_name, "value": r.id} for r in roles]
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
        Output(ID_CREATE_PAGES_CHECKLIST, "value", allow_duplicate=True),
        Output("rbac-refresh", "data", allow_duplicate=True),
    ],
    [Input("create-role-btn", "n_clicks")],
    [
        add_state_user_id(),
        State("new-role-name", "value"),
        State(ID_CREATE_PAGES_CHECKLIST, "value"),
        State(ID_CREATE_IS_ADMIN_CHECKBOX, "value"),
        State(ID_CREATE_ALTER_FILE_CHECKBOX, "value"),
    ],
    prevent_initial_call=True,
)
def create_role_with_pages(
    n_clicks, user_id, role_name, selected_ids, is_admin, alter_file
):
    if not n_clicks:
        raise PreventUpdate
    if user_id is None:
        return dash.no_update
    if not role_name:
        return (
            "Please enter a role name",
            True,
            "danger",
            dash.no_update,
            dash.no_update,
            dash.no_update,
        )

    if not selected_ids and not alter_file:
        return (
            "Please select at least one page",
            True,
            "danger",
            dash.no_update,
            dash.no_update,
            dash.no_update,
        )

    with session_scope() as session:
        existing = role_service.get_role_by_name(role_name, session)
        if existing:
            return (
                f"Role {role_name} already exists",
                True,
                "warning",
                dash.no_update,
                dash.no_update,
                dash.no_update,
            )

        new_role = role_service.create_role(
            role_name=role_name,
            session=session,
            is_admin=is_admin,
            created_by=user_id,
            change_file=alter_file,
        )
        if not is_admin:
            pages_ids_without_admin = get_all_metadata_id_pages_dynamic(False)
            selected_ids = [id for id in selected_ids if id in pages_ids_without_admin]

        pages_to_assign = page_service.get_pages_by_id(selected_ids, session)

        role_service.assign_pages_to_role(new_role, pages_to_assign, session)

        return (
            f"Role {role_name} created with {len(pages_to_assign)} pages",
            True,
            "success",
            "",
            [],
            {"refresh": True},
        )


# ==================== EDIT ROLE CALLBACKS ====================


@app.callback(
    [
        Output("edit-roles-alert", "children"),
        Output("edit-roles-alert", "is_open"),
        Output("edit-roles-alert", "color"),
        Output("rbac-refresh", "data", allow_duplicate=True),
    ],
    [Input("update-perms-btn", "n_clicks")],
    [
        State(ID_SELECT_ROLE, "value"),
        State(ID_EDIT_PAGES_CHECKLIST, "value"),
        State(ID_EDIT_IS_ADMIN_CHECKBOX, "value"),
        State(ID_EDIT_ALTER_FILE_CHECKBOX, "value"),
    ],
    prevent_initial_call=True,
)
def update_role_pages(n_clicks, role_id, selected_ids, is_admin, alter_file):
    if not n_clicks or not role_id:
        raise PreventUpdate
    if not selected_ids:
        return ("No pages selected", True, "warning", dash.no_update)

    if not is_admin:
        pages_ids_without_admin = get_all_metadata_id_pages_dynamic(False)
        selected_ids = [id for id in selected_ids if id in pages_ids_without_admin]

    with session_scope() as session:
        role = role_service.get_role_by_id(role_id, session)
        if not role:
            return (f"Role {role_id} not found", True, "danger", dash.no_update)

        pages = page_service.get_pages_by_id(selected_ids, session)

        role_service.update_role(
            role_id, session, is_admin=is_admin, change_file=alter_file
        )
        role_service.assign_pages_to_role(role, pages, session)

        return (
            f"Updated role with {len(selected_ids)} pages",
            True,
            "success",
            {"refresh": True},
        )


@app.callback(
    [
        Output("edit-roles-alert", "children", allow_duplicate=True),
        Output("edit-roles-alert", "is_open", allow_duplicate=True),
        Output("edit-roles-alert", "color", allow_duplicate=True),
        Output(ID_SELECT_ROLE, "value"),
        Output("rbac-refresh", "data", allow_duplicate=True),
    ],
    [Input("edit-delete-role-btn", "n_clicks")],
    [State(ID_SELECT_ROLE, "value")],
    prevent_initial_call=True,
)
def delete_role(n_clicks, role_name):
    if not n_clicks or not role_name:
        raise PreventUpdate
    if role_name == "admin":
        return (
            "Cannot delete admin role",
            True,
            "warning",
            dash.no_update,
            dash.no_update,
        )
    try:
        with session_scope() as db_session:
            role = role_service.get_role_by_name(role_name, db_session)
            if not role:
                return (
                    f"Role {role_name} not found",
                    True,
                    "danger",
                    dash.no_update,
                    dash.no_update,
                )
            if getattr(role, "users", None):
                return (
                    f"Cannot delete role with {len(role.users)} users",
                    True,
                    "warning",
                    dash.no_update,
                    dash.no_update,
                )

            success = role_service.delete_role(role.id, 0, db_session)
            if success:
                return (
                    f"Role {role_name} deleted",
                    True,
                    "success",
                    None,
                    {"refresh": True},
                )
            else:
                return (
                    "Failed to delete role",
                    True,
                    "danger",
                    dash.no_update,
                    dash.no_update,
                )
    except Exception as e:
        logging.error(f"Error deleting role: {e}")
        return f"Error: {str(e)}", True, "danger", dash.no_update, dash.no_update


# ==================== USER TABLE CALLBACKS ====================
@app.callback(
    Output("users-table", "data"),
    [
        Input("users-interval", "n_intervals"),
        Input("rbac-refresh", "data"),
    ],
    prevent_initial_call=False,
)
def update_users_table(_, __):
    with session_scope(False) as db_session:
        users = user_service.get_all_users(db_session)
        table_data = []
        role_ids = {user.role_id for user in users}
        roles = role_service.get_roles_by_ids(role_ids, db_session)

        name_roles = {role.id: role.role_name for role in roles}
        for u in users:
            created_by = u.created_by
            creator_source = created_by if created_by is not None else "system"
            row = {
                "id": u.id,
                "email": u.email,
                "role": name_roles[u.role_id] or "No Role",
                "role_id": u.role_id,
                "disabled": u.disabled,
                "created_at": u.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "created_by": creator_source,
            }

            table_data.append(row)
    return table_data


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
def show_confirm_modal(
    enable_clicks, disable_clicks, delete_clicks, selected_rows, table_data
):
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
        message, action = (
            f"Delete user {selected_user['email']}? This action cannot be undone.",
            "delete",
        )
    else:
        raise PreventUpdate

    return (
        True,
        message,
        {
            "action": action,
            "user_id": selected_user["id"],
            "disabled": selected_user["disabled"],
        },
    )


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
    if not n_clicks or not pending_action:
        raise PreventUpdate

    action = pending_action["action"]
    user_id = pending_action["user_id"]

    if action == "enable":

        return enable_user(user_id)
    elif action == "disable":
        return disable_user(user_id)
    elif action == "delete":
        return delete_user(user_id)
    return "Unknown action", True, "danger", False, dash.no_update


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
def assign_role_to_user(n_clicks, role_id, selected_rows, table_data):
    if not n_clicks or not role_id or not selected_rows:
        raise PreventUpdate
    selected_user = table_data[selected_rows[0]]
    try:
        with session_scope() as db_session:
            role = role_service.get_role_by_id(role_id, db_session)
            if not role:
                return f"Role {role_id} not found", True, "danger", dash.no_update
            user = user_service.update_user(
                selected_user["id"], db_session, role_id=role.id
            )
            if user:
                return (
                    f"Assigned {role.role_name} to {selected_user['email']}",
                    True,
                    "success",
                    {"refresh": True},
                )
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


@app.callback(
    Output(ID_EDIT_PAGES_CHECKLIST, "value"),
    Output(ID_EDIT_IS_ADMIN_CHECKBOX, "value"),
    Output(ID_EDIT_ALTER_FILE_CHECKBOX, "value"),
    Input(ID_SELECT_ROLE, "value"),
    State(ID_CREATE_PAGES_CHECKLIST, "options"),
)
def update_page_visibility_controls(role_id, opts):

    if role_id is None or not opts:
        return [], False, False
    with session_scope(False) as session:
        role = role_service.get_role_by_id(role_id, session)

        allowed_pages_ids = [allowed_page.id for allowed_page in role.pages]

    return allowed_pages_ids, role.is_admin, role.change_file


@app.callback(
    [
        Output("btn-enable", "disabled"),
        Output("btn-disable", "disabled"),
        Output("btn-delete", "disabled"),
        Output("assign-role-btn", "disabled"),
        Output("assign-role-select", "disabled"),
        Output("assign-role-select", "value"),
    ],
    Input("users-table", "selected_rows"),
    State("users-table", "data"),
)
def toggle_action_buttons(selected_rows, table_data):
    # Default: all buttons disabled
    if not selected_rows:
        return True, True, True, True, True, None

    row_index = selected_rows[0]
    selected_row = table_data[row_index]
    is_disabled = selected_row["disabled"]
    created_by = selected_row["created_by"]
    role_id = selected_row["role_id"]

    # Enable button logic:
    # - Enable "Enable" button only if the user is disabled
    enable_btn_disabled = not is_disabled

    # Disable button logic:
    # - Enable "Disable" button only if the user is enabled
    disable_btn_disabled = is_disabled

    # Delete button logic:
    # - Disable delete if created_by is None
    delete_btn_disabled = created_by == "system"

    return (
        enable_btn_disabled,
        disable_btn_disabled,
        delete_btn_disabled,
        False,
        False,
        str(role_id),
    )
