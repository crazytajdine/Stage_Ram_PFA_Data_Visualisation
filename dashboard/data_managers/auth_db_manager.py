# dashboard/data_managers/auth_db_manager.py
import logging
from typing import Any, Dict, List, Optional, Sequence

from sqlalchemy import text

try:
    from .database_manager import get_engine
except ImportError:
    from dashboard.data_managers.database_manager import get_engine

import bcrypt

ADVISORY_LOCK_KEY = 946_870_521


class AuthDatabaseManager:
    """
    Pure role-based RBAC:
      - users.role: arbitrary string (e.g., 'admin', 'perf', 'ops'…)
      - roles(role TEXT PRIMARY KEY)
      - role_permissions(role TEXT, page_slug TEXT, UNIQUE(role,page_slug))

    Admin is a special role: not restricted by role_permissions.
    """

    def __init__(self) -> None:
        self.engine = get_engine()
        self.dialect = self.engine.dialect.name  # 'postgresql' | 'sqlite' | ...
        self.schema_prefix = "public." if self.dialect == "postgresql" else ""
        self.users_table = f"{self.schema_prefix}users"
        self.roles_table = f"{self.schema_prefix}roles"
        self.role_permissions_table = f"{self.schema_prefix}role_permissions"
        self._init_db()

    # -------------------- Init / DDL --------------------
    def _init_db(self) -> None:
        with self.engine.begin() as conn:
            if self.dialect == "postgresql":
                conn.execute(
                    text("SELECT pg_advisory_lock(:k)"), {"k": ADVISORY_LOCK_KEY}
                )
            try:
                if self.dialect == "postgresql":
                    conn.execute(text("CREATE SCHEMA IF NOT EXISTS public"))

                # USERS (no CHECK constraint on role)
                if self.dialect == "postgresql":
                    conn.execute(
                        text(
                            f"""
                        CREATE TABLE IF NOT EXISTS {self.users_table} (
                          id SERIAL PRIMARY KEY,
                          email TEXT NOT NULL UNIQUE,
                          password_hash TEXT NOT NULL,
                          role TEXT NOT NULL,
                          is_active BOOLEAN NOT NULL DEFAULT TRUE,
                          created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                          created_by TEXT
                        )
                    """
                        )
                    )
                    # attempt to drop any old CHECK constraints on role
                    tbl = f"{self.users_table}"
                    drop_sql = f"""
                    DO $$
                    DECLARE
                      r RECORD;
                    BEGIN
                      FOR r IN
                        SELECT conname
                        FROM pg_constraint
                        WHERE conrelid = to_regclass('{tbl}')
                          AND contype = 'c'
                      LOOP
                        EXECUTE format('ALTER TABLE {tbl} DROP CONSTRAINT %I', r.conname);
                      END LOOP;
                    END$$;
                    """
                    conn.execute(text(drop_sql))
                else:
                    conn.execute(
                        text(
                            """
                        CREATE TABLE IF NOT EXISTS users (
                          id INTEGER PRIMARY KEY AUTOINCREMENT,
                          email TEXT NOT NULL UNIQUE,
                          password_hash TEXT NOT NULL,
                          role TEXT NOT NULL,
                          is_active INTEGER NOT NULL DEFAULT 1,
                          created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                          created_by TEXT
                        )
                    """
                        )
                    )
                    # NOTE: If you previously created a CHECK in SQLite, easiest is to recreate the DB.

                # ROLES
                if self.dialect == "postgresql":
                    conn.execute(
                        text(
                            f"""
                        CREATE TABLE IF NOT EXISTS {self.roles_table} (
                          role TEXT PRIMARY KEY,
                          created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                          created_by TEXT
                        )
                    """
                        )
                    )
                else:
                    conn.execute(
                        text(
                            """
                        CREATE TABLE IF NOT EXISTS roles (
                          role TEXT PRIMARY KEY,
                          created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                          created_by TEXT
                        )
                    """
                        )
                    )

                # ROLE PERMISSIONS
                if self.dialect == "postgresql":
                    conn.execute(
                        text(
                            f"""
                        CREATE TABLE IF NOT EXISTS {self.role_permissions_table} (
                          role TEXT NOT NULL REFERENCES {self.roles_table}(role) ON DELETE CASCADE,
                          page_slug TEXT NOT NULL,
                          UNIQUE(role, page_slug)
                        )
                    """
                        )
                    )
                else:
                    conn.execute(
                        text(
                            """
                        CREATE TABLE IF NOT EXISTS role_permissions (
                          role TEXT NOT NULL,
                          page_slug TEXT NOT NULL,
                          UNIQUE(role, page_slug)
                        )
                    """
                        )
                    )

                # seed admin role & default admin user
                # ensure 'admin' role exists
                self._ensure_role_exists(conn, "admin", "system")
                # also a common default role 'user' for convenience
                self._ensure_role_exists(conn, "user", "system")

                count = conn.execute(
                    text(f"SELECT COUNT(*) FROM {self.users_table}")
                ).scalar_one()
                if not count:
                    pw_hash = bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode(
                        "utf-8"
                    )
                    conn.execute(
                        text(
                            f"""
                            INSERT INTO {self.users_table} (email, password_hash, role, is_active, created_by)
                            VALUES (:e, :p, 'admin', TRUE, 'system')
                        """
                        ),
                        {"e": "admin@company.com", "p": pw_hash},
                    )
            finally:
                if self.dialect == "postgresql":
                    conn.execute(
                        text("SELECT pg_advisory_unlock(:k)"), {"k": ADVISORY_LOCK_KEY}
                    )

    # -------------------- Helpers --------------------
    def _to_bool(self, v: Any) -> bool:
        return bool(v)

    def _row_to_user(self, row: Any) -> Dict[str, Any]:
        if row is None:
            return {}
        d = dict(row._mapping) if hasattr(row, "_mapping") else dict(row)
        if "is_active" in d:
            d["is_active"] = self._to_bool(d["is_active"])
        return d

    def _ensure_role_exists(self, conn, role: str, created_by: str = "system") -> None:
        r = (role or "").strip().lower()
        if not r:
            return
        exists = conn.execute(
            text(f"SELECT 1 FROM {self.roles_table} WHERE role=:r"), {"r": r}
        ).first()
        if not exists:
            conn.execute(
                text(
                    f"INSERT INTO {self.roles_table} (role, created_by) VALUES (:r, :c)"
                ),
                {"r": r, "c": created_by or "system"},
            )

    # -------------------- Users API --------------------
    def verify_user(self, email: str, password: str) -> bool:
        if not email:
            return False
        email_norm = email.strip().lower()
        with self.engine.begin() as conn:
            row = conn.execute(
                text(
                    f"SELECT password_hash, is_active FROM {self.users_table} WHERE email=:e"
                ),
                {"e": email_norm},
            ).first()
        if not row:
            return False
        pw_hash, is_active = row
        if not self._to_bool(is_active):
            return False
        try:
            return bcrypt.checkpw(password.encode("utf-8"), pw_hash.encode("utf-8"))
        except Exception:
            logging.exception("bcrypt check failed")
            return False

    def get_user_by_email(self, email: str) -> Dict[str, Any]:
        if not email:
            return {}
        email_norm = email.strip().lower()
        with self.engine.begin() as conn:
            row = conn.execute(
                text(
                    f"""
                    SELECT id, email, role, is_active, created_at, created_by
                    FROM {self.users_table}
                    WHERE email=:e
                """
                ),
                {"e": email_norm},
            ).first()
        return self._row_to_user(row) if row else {}

    def get_all_users(self) -> List[Dict[str, Any]]:
        with self.engine.begin() as conn:
            rows = conn.execute(
                text(
                    f"""
                    SELECT id, email, role, is_active, created_at, created_by
                    FROM {self.users_table}
                    ORDER BY created_at DESC, id DESC
                """
                )
            ).fetchall()
        return [self._row_to_user(r) for r in rows]

    def create_user(
        self, email: str, password: str, role: str, created_by: str = "system"
    ) -> int:
        email_norm = (email or "").strip().lower()
        r = (role or "").strip().lower()
        if not email_norm or not password or not r:
            raise ValueError("Email, password and role are required.")

        pw_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode(
            "utf-8"
        )

        with self.engine.begin() as conn:
            self._ensure_role_exists(conn, r, created_by)
            res = conn.execute(
                (
                    text(
                        f"""
                    INSERT INTO {self.users_table} (email, password_hash, role, is_active, created_by)
                    VALUES (:e, :p, :r, TRUE, :c)
                    RETURNING id
                """
                    )
                    if self.dialect == "postgresql"
                    else text(
                        f"""
                    INSERT INTO {self.users_table} (email, password_hash, role, is_active, created_by)
                    VALUES (:e, :p, :r, 1, :c)
                """
                    )
                ),
                {"e": email_norm, "p": pw_hash, "r": r, "c": created_by or "system"},
            )
            if self.dialect == "postgresql":
                new_id = res.scalar_one()
            else:
                new_id = conn.execute(text("SELECT last_insert_rowid()")).scalar_one()
        return int(new_id)

    def set_active(self, user_id: int, is_active: bool) -> None:
        with self.engine.begin() as conn:
            conn.execute(
                text(f"UPDATE {self.users_table} SET is_active=:a WHERE id=:i"),
                {"a": bool(is_active), "i": int(user_id)},
            )

    def delete_user(self, user_id: int) -> None:
        uid = int(user_id)
        with self.engine.begin() as conn:
            role_row = conn.execute(
                text(f"SELECT role, is_active FROM {self.users_table} WHERE id=:i"),
                {"i": uid},
            ).first()
            if not role_row:
                return
            role, is_active = role_row
            if role == "admin" and self._to_bool(is_active):
                active_admins = conn.execute(
                    text(
                        f"SELECT COUNT(*) FROM {self.users_table} WHERE role='admin' AND is_active"
                    )
                    if self.dialect == "postgresql"
                    else text(
                        f"SELECT COUNT(*) FROM {self.users_table} WHERE role='admin' AND is_active=1"
                    )
                ).scalar_one()
                if int(active_admins) <= 1:
                    raise ValueError("Cannot delete the last active admin.")
            conn.execute(
                text(f"DELETE FROM {self.users_table} WHERE id=:i"), {"i": uid}
            )

    def assign_user_role(self, user_id: int, role: str) -> None:
        r = (role or "").strip().lower()
        if not r:
            raise ValueError("Role is required.")
        with self.engine.begin() as conn:
            self._ensure_role_exists(conn, r)
            conn.execute(
                text(f"UPDATE {self.users_table} SET role=:r WHERE id=:i"),
                {"r": r, "i": int(user_id)},
            )

    # -------------------- Roles & Permissions API --------------------
    def list_roles(self) -> List[str]:
        with self.engine.begin() as conn:
            rows = conn.execute(
                text(f"SELECT role FROM {self.roles_table} ORDER BY role ASC")
            ).fetchall()
        return [r[0] for r in rows]

    def create_role(self, role: str, created_by: str = "system") -> None:
        r = (role or "").strip().lower()
        if not r:
            raise ValueError("Role name is required.")
        with self.engine.begin() as conn:
            self._ensure_role_exists(conn, r, created_by)

    def delete_role(self, role: str) -> None:
        r = (role or "").strip().lower()
        if not r:
            return
        if r in {"admin"}:
            raise ValueError("Cannot delete 'admin' role.")
        with self.engine.begin() as conn:
            used = conn.execute(
                text(f"SELECT COUNT(*) FROM {self.users_table} WHERE role=:r"),
                {"r": r},
            ).scalar_one()
            if used:
                raise ValueError("Cannot delete role while users are assigned to it.")
            conn.execute(
                text(f"DELETE FROM {self.role_permissions_table} WHERE role=:r"),
                {"r": r},
            )
            conn.execute(
                text(f"DELETE FROM {self.roles_table} WHERE role=:r"), {"r": r}
            )

    def get_role_permissions(self, role: Optional[str]) -> List[str]:
        if not role or role == "admin":
            return []  # admin unrestricted
        r = role.strip().lower()
        with self.engine.begin() as conn:
            rows = conn.execute(
                text(
                    f"SELECT page_slug FROM {self.role_permissions_table} WHERE role=:r ORDER BY page_slug"
                ),
                {"r": r},
            ).fetchall()
        return [row[0] for row in rows]

    def set_role_permissions(self, role: str, page_slugs: Sequence[str]) -> None:
        r = (role or "").strip().lower()
        if not r:
            raise ValueError("Role is required.")
        if r == "admin":
            # admin permissions are implicit; ignore
            return
        slugs = sorted({(s or "").strip() for s in page_slugs if (s or "").strip()})
        with self.engine.begin() as conn:
            self._ensure_role_exists(conn, r)
            conn.execute(
                text(f"DELETE FROM {self.role_permissions_table} WHERE role=:r"),
                {"r": r},
            )
            for s in slugs:
                conn.execute(
                    text(
                        f"INSERT INTO {self.role_permissions_table} (role, page_slug) VALUES (:r, :s)"
                    ),
                    {"r": r, "s": s},
                )

    def get_allowed_pages_for_role(self, role: Optional[str]) -> List[str]:
        return self.get_role_permissions(role)
