from datetime import datetime
from typing import Optional
import logging
from schemas.database_models import Role
from data_managers.database_manager import run_in_session
from sqlalchemy.orm import Session


def create_role(role_name: str, created_by: int) -> Optional[Role]:

    def logic(s: Session) -> Optional[Role]:
        role = Role(
            role_name=role_name,
            created_at=datetime.now(),
            created_by=created_by,
        )
        s.add(role)
        logging.info(f"User {created_by} created role '{role_name}'")
        return role

    return run_in_session(logic, commit=True)


def get_role_by_id(role_id: int) -> Optional[Role]:
    return run_in_session(
        lambda s: s.query(Role).filter(Role.id == role_id).one_or_none()
    )


def get_role_by_name(role_name: str) -> Optional[Role]:
    return run_in_session(
        lambda s: s.query(Role).filter(Role.role_name == role_name).one_or_none()
    )


def update_role(role_id: int, new_name: str, performed_by: int) -> Optional[Role]:
    def logic(s: Session) -> Optional[Role]:
        role = s.query(Role).filter(Role.id == role_id).one_or_none()
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

    return run_in_session(logic, commit=True)


def delete_role(role_id: int, performed_by: int) -> bool:
    def logic(s):
        role = s.query(Role).filter(Role.id == role_id).one_or_none()
        if role is None:
            logging.warning(
                f"User {performed_by} attempted to delete role id={role_id}, but role not found"
            )
            return False
        s.delete(role)
        logging.info(f"User {performed_by} deleted role id={role_id}")
        return True

    return run_in_session(logic, commit=True, default=False)
