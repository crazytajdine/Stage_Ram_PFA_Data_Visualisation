from datetime import datetime
from typing import List, Optional, Set
import logging
from sqlalchemy.orm import Session
from schemas.database_models import Page, Role


def create_role(
    role_name: str,
    session: Session,
    created_by: Optional[int] = None,
    is_admin=False,
    change_file=False,
    id=None,
) -> Role:
    role = Role(
        id=id,
        role_name=role_name,
        created_at=datetime.now(),
        created_by=created_by,
        is_admin=is_admin,
        change_file=change_file,
    )
    session.add(role)
    session.flush()
    logging.info(f"User {created_by} created role '{role_name}'")
    return role


def update_role(role_id: int, session: Session, **kwargs) -> Optional[Role]:
    role = session.query(Role).filter(Role.id == role_id).one_or_none()
    if not role:
        logging.warning(f"Role id={role_id} not found for update")
        return None
    for k, v in kwargs.items():
        if hasattr(role, k):
            setattr(role, k, v)
    logging.info(f"Role user id={role_id}: {list(kwargs.keys())}")
    return role


def assign_pages_to_role(role: Role, pages: list[Page], session: Session):
    role.pages = pages
    logging.info(f"Assigned {len(pages)} pages to role '{role.role_name}'")

    session.flush()


def get_role_by_id(role_id: int, session: Session) -> Optional[Role]:
    return session.query(Role).filter(Role.id == role_id).one_or_none()


def get_roles_by_ids(role_ids: Set[int], session: Session) -> List[Role]:
    return session.query(Role).filter(Role.id.in_(role_ids)).all()


def get_roles(session: Session) -> List[Role]:
    return session.query(Role).all()


def get_role_by_name(role_name: str, session: Session) -> Optional[Role]:
    return session.query(Role).filter(Role.role_name == role_name).one_or_none()


def get_pages_with_role_id(role_id: str, session: Session) -> List[Page]:
    role = get_role_by_id(role_id, session)
    if not role:
        return []
    return role.pages


def delete_role(role_id: int, performed_by: int, session: Session) -> bool:
    role = session.query(Role).filter(Role.id == role_id).one_or_none()
    if not role:
        logging.warning(
            f"User {performed_by} attempted to delete role id={role_id}, but role not found"
        )
        return False
    session.delete(role)
    logging.info(f"User {performed_by} deleted role id={role_id}")
    return True
