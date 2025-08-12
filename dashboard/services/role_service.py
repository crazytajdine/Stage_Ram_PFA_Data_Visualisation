from datetime import datetime
from typing import Optional
import logging
from schemas.database_models import Role
from data_managers.database_manager import session_scope


def create_role(role_name: str, created_by: int) -> Role:
    with session_scope() as session:
        role = Role(
            role_name=role_name,
            created_at=datetime.now(),
            created_by=created_by,
        )
        session.add(role)
        session.flush()
        logging.info(f"User {created_by} created role '{role_name}'")
        return role


def get_role_by_id(role_id: int) -> Optional[Role]:
    with session_scope() as session:
        role = session.query(Role).filter(Role.id == role_id).one_or_none()
        if role:
            logging.info(f"Role id={role_id} retrieved")
        else:
            logging.warning(f"Role id={role_id} not found")
        return role


def get_role_by_name(role_name: str) -> Optional[Role]:
    with session_scope() as session:
        role = session.query(Role).filter(Role.role_name == role_name).one_or_none()
        if role:
            logging.info(f"Role '{role_name}' retrieved")
        else:
            logging.warning(f"Role '{role_name}' not found")
        return role


def update_role(role_id: int, new_name: str, performed_by: int) -> Optional[Role]:
    with session_scope() as session:
        role = session.query(Role).filter(Role.id == role_id).one_or_none()
        if role is None:
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


def delete_role(role_id: int, performed_by: int) -> bool:
    with session_scope() as session:
        role = session.query(Role).filter(Role.id == role_id).one_or_none()
        if role is None:
            logging.warning(
                f"User {performed_by} attempted to delete role id={role_id}, but role not found"
            )
            return False
        session.delete(role)
        logging.info(f"User {performed_by} deleted role id={role_id}")
        return True
