from datetime import datetime
from typing import Optional
import logging
from sqlalchemy.orm import Session
from schemas.database_models import Role


def create_role(
    role_name: str, session: Session, created_by: Optional[int] = None
) -> Role:
    role = Role(
        role_name=role_name,
        created_at=datetime.now(),
        created_by=created_by,
    )
    session.add(role)
    session.flush()
    logging.info(f"User {created_by} created role '{role_name}'")
    return role


def get_role_by_id(role_id: int, session: Session) -> Optional[Role]:
    return session.query(Role).filter(Role.id == role_id).one_or_none()


def get_role_by_name(role_name: str, session: Session) -> Optional[Role]:
    return session.query(Role).filter(Role.role_name == role_name).one_or_none()


def update_role(
    role_id: int, new_name: str, performed_by: int, session: Session
) -> Optional[Role]:
    role = session.query(Role).filter(Role.id == role_id).one_or_none()
    if not role:
        logging.warning(
            f"User {performed_by} attempted to update role id={role_id}, but role not found"
        )
        return None
    old_name = role.role_name
    role.role_name = new_name
    logging.info(
        f"User {performed_by} updated role id={role_id} from '{old_name}' to '{new_name}'"
    )
    return role


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
