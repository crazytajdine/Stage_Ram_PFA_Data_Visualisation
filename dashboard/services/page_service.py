from typing import List, Optional, Iterable, Set
import logging
import re

from sqlalchemy import Row, case, update, delete, insert
from sqlalchemy.orm import Session

from schemas.database_models import Page, User, role_page_table

# ── Use utils_page to validate IDs against NAV_CONFIG (if available) ──────────
try:
    from utils_dashboard.utils_page import (
        get_all_metadata_id_pages_dynamic as _valid_nav_ids,
    )
except Exception:

    def _valid_nav_ids() -> List[int]:
        return []  # if utils_page is unavailable, skip validation


# NAV_CONFIG is used to resolve page NAME -> numeric ID for backward-compat APIs
try:
    from configurations.nav_config import NAV_CONFIG
except Exception:
    NAV_CONFIG = []


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip()).lower()


def _name_to_id(name: str) -> Optional[int]:
    """
    Resolve a navbar 'name' to its numeric id from NAV_CONFIG.
    Returns None if not found or id is None.
    """
    target = _norm(name)
    for item in NAV_CONFIG:
        if getattr(item, "id", None) is None:
            continue
        nm = getattr(item, "name", None)
        if nm and _norm(nm) == target:
            return int(item.id)
    return None


# ──────────────────────────────────────────────────────────────────────────────
# Backward-compatible name-based APIs (shims)
# ──────────────────────────────────────────────────────────────────────────────


def get_page_by_name(name: str, session: Session) -> Optional[Page]:
    """
    Compatibility shim: look up by 'name' via NAV_CONFIG, then fetch by id.
    """
    pid = _name_to_id(name)
    if pid is None:
        logging.warning(
            f"get_page_by_name: unknown page name {name!r} (not in NAV_CONFIG)"
        )
        return None
    return get_page_by_id(pid, session)


def get_pages_by_name(names: List[str], session: Session) -> List[Page]:
    ids = []
    for n in names or []:
        pid = _name_to_id(n)
        if pid is not None:
            ids.append(pid)
    return get_pages_by_id(ids, session) if ids else []


# ──────────────────────────────────────────────────────────────────────────────
# Helpers (private)
# ──────────────────────────────────────────────────────────────────────────────


def _coerce_int(x) -> Optional[int]:
    """Accept int/str; return int or None if not coercible."""
    if x is None:
        return None
    try:
        return int(x)
    except Exception:
        return None


def _filter_valid_ids(ids: Iterable[int]) -> List[int]:
    """Deduplicate and, if NAV ids are known, keep only those."""
    ids_set: Set[int] = {i for i in (_coerce_int(v) for v in ids) if i is not None}
    nav = set(_valid_nav_ids() or [])
    if nav:
        invalid = sorted(ids_set - nav)
        if invalid:
            logging.warning(f"Ignoring unknown page ids (not in NAV_CONFIG): {invalid}")
        ids_set &= nav
    return sorted(ids_set)


# ──────────────────────────────────────────────────────────────────────────────
# Public API (names/signatures unchanged)
# ──────────────────────────────────────────────────────────────────────────────


def create_page(page_id: str, session: Session) -> Page:
    """
    Create a single Page row by ID if missing; return the Page.
    Signature unchanged. Accepts int-like string OR a NAME (mapped via NAV_CONFIG).
    """
    # try int first
    try:
        pid = int(page_id)
    except Exception:
        # not an int -> try resolving as navbar NAME
        pid = _name_to_id(str(page_id))
        if pid is None:
            raise ValueError(
                f"create_page: page_id must be int-like or a known NAV name, got {page_id!r}"
            )

    existing = session.query(Page).filter(Page.id == pid).one_or_none()
    if existing:
        return existing

    page = Page(id=pid)
    session.add(page)
    session.flush()
    logging.info(f"Page '{page.id}' created")
    return page


def create_pages(page_ids: List[int], session: Session) -> List[Page]:
    """
    Idempotent bulk creation: only creates missing IDs, returns all requested Pages.
    Name/signature unchanged.
    """
    ids = _filter_valid_ids(page_ids)
    if not ids:
        return []

    existing_ids = {i for (i,) in session.query(Page.id).filter(Page.id.in_(ids)).all()}
    missing = [i for i in ids if i not in existing_ids]

    if missing:
        session.bulk_save_objects([Page(id=i) for i in missing])
        session.flush()
        logging.info(f"Created {len(missing)} new pages: {missing}")

    return session.query(Page).filter(Page.id.in_(ids)).all()


def get_pages(session: Session) -> list[Page]:
    return session.query(Page).all()


def get_pages_by_id(ids: List[int], session: Session) -> List[Page]:
    ids = _filter_valid_ids(ids)
    if not ids:
        return []
    return session.query(Page).filter(Page.id.in_(ids)).all()


def get_page_by_id(page_id: int, session: Session) -> Optional[Page]:
    pid = _coerce_int(page_id)
    if pid is None:
        return None
    return session.query(Page).filter(Page.id == pid).one_or_none()


def delete_page(page_id: int, session: Session) -> bool:
    pid = _coerce_int(page_id)
    if pid is None:
        logging.warning(f"Attempted to delete page with non-int id: {page_id!r}")
        return False

    page = session.query(Page).filter(Page.id == pid).one_or_none()
    if not page:
        logging.warning(f"Attempted to delete page id={pid}, but page not found")
        return False

    session.delete(page)
    logging.info(f"Deleted page id={pid}")
    return True


def get_user_allowed_pages_with_preferences(
    user_id: int, session: Session
) -> list[Row]:
    """
    Returns raw association rows where disabled = False (unchanged API).
    Each Row has columns: role_id, page_id, disabled (and any others in the table).
    """
    return (
        session.query(role_page_table)
        .join(User, User.role_id == role_page_table.c.role_id)
        .filter(User.id == user_id, role_page_table.c.disabled.is_(False))
        .all()
    )


def get_user_allowed_pages_all(user_id: int, session: Session) -> list[Row]:
    """
    Returns raw association rows (enabled + disabled), unchanged API.
    """
    return (
        session.query(role_page_table)
        .join(User, User.role_id == role_page_table.c.role_id)
        .filter(User.id == user_id)
        .all()
    )


def update_user_page_preferences(
    user_id: int, preferences: dict[int, bool], session: Session
) -> bool:
    if not preferences:
        return False

    case_stmt = case(
        preferences,
        value=role_page_table.c.page_id,
    )

    stmt = (
        update(role_page_table)
        .where(role_page_table.c.role_id == User.role_id)
        .where(User.id == user_id)
        .values(disabled=case_stmt)
    )

    session.execute(stmt)
    session.commit()

    return True


# ──────────────────────────────────────────────────────────────────────────────
# Optional extras (NEW helpers; safe to import if you want)
# ──────────────────────────────────────────────────────────────────────────────


def set_role_pages_by_ids(
    role_id: int,
    page_ids: Iterable[int],
    session: Session,
    disabled_default: bool = False,
) -> None:
    """
    Convenience helper for your admin page:
      - validates IDs against NAV_CONFIG (if available)
      - ensures Page rows exist
      - replaces existing role↔page rows in role_page_table
    """
    ids = _filter_valid_ids(page_ids)
    create_pages(ids, session)  # idempotent

    # Clear existing
    session.execute(delete(role_page_table).where(role_page_table.c.role_id == role_id))

    # Insert new links
    if ids:
        session.execute(
            insert(role_page_table),
            [
                {"role_id": role_id, "page_id": i, "disabled": disabled_default}
                for i in ids
            ],
        )

    session.flush()
    logging.info(f"Role {role_id}: set {len(ids)} page permissions -> {ids}")


def sync_pages_with_nav(session: Session) -> int:
    """
    Ensure DB has a Page row for every NAV_CONFIG id (via utils_page).
    Returns number created. Safe to call at startup.
    """
    nav = set(_valid_nav_ids() or [])
    if not nav:
        return 0
    existing = {i for (i,) in session.query(Page.id).filter(Page.id.in_(nav)).all()}
    missing = sorted(nav - existing)
    if missing:
        session.bulk_save_objects([Page(id=i) for i in missing])
        session.flush()
        logging.info(f"sync_pages_with_nav: created {len(missing)} pages: {missing}")
    return len(missing)
