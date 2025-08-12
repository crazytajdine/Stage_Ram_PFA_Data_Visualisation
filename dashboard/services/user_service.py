from datetime import datetime
from typing import Optional, List
import logging
from schemas.database_models import User, Option
from data_managers.database_manager import session_scope
import bcrypt


def create_user(
    email: str,
    password: str,
    role_id: int,
    created_by: Optional[int] = None,
    new_option: Option = None,
    commit: bool = True,
) -> User:
    with session_scope(commit) as session:

        user = User(
            email=email,
            password=password,
            role_id=role_id,
            created_at=datetime.now(),
            created_by=created_by,
            option=new_option,
        )
        session.add(user)
        session.flush()
        logging.info(f"Created user {email} with id {user.id} by creator {created_by}")
        return user


def get_user_by_id(user_id: int) -> Optional[User]:
    with session_scope() as session:
        user = session.query(User).filter(User.id == user_id).one_or_none()
        if user:
            logging.info(f"Found user with id {user_id}")
        else:
            logging.warning(f"User with id {user_id} not found")
        return user


def get_user_by_email(email: str) -> Optional[User]:
    with session_scope() as session:
        user = session.query(User).filter(User.email == email).one_or_none()
        if user:
            logging.info(f"Found user with email {email}")
        else:
            logging.warning(f"User with email {email} not found")
        return user


def get_users_created_by(user_id: int) -> List[User]:
    with session_scope() as session:
        users = session.query(User).filter(User.created_by == user_id).all()
        logging.info(f"Found {len(users)} users created by user {user_id}")
        return users


def update_user(user_id: int, **kwargs) -> Optional[User]:
    with session_scope() as session:
        user = session.query(User).filter(User.id == user_id).one_or_none()
        if user is None:
            logging.warning(f"User with id {user_id} not found for update")
            return None

        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
        logging.info(f"Updated user {user_id} with fields {list(kwargs.keys())}")
        return user


def delete_user(user_id: int) -> bool:
    with session_scope() as session:
        user = session.query(User).filter(User.id == user_id).one_or_none()
        if user is None:
            logging.warning(f"User with id {user_id} not found for deletion")
            return False
        session.delete(user)
        logging.info(f"Deleted user with id {user_id}")
        return True


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), hashed_password.encode("utf-8")
        )
    except Exception as e:
        logging.error(f"Password verification failed: {e}")
        return False
