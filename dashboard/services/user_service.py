from datetime import datetime
from typing import Optional, List
import logging
import bcrypt
from schemas.database_models import User, Option
from data_managers.database_manager import run_in_session
from sqlalchemy.orm import Session


def create_user(
    email: str,
    password: str,
    role_id: int,
    created_by: Optional[int] = None,
    new_option: Optional[Option] = None,
) -> Optional[User]:

    def logic(s: Session) -> Optional[User]:
        user = User(
            email=email,
            password=password,
            role_id=role_id,
            created_at=datetime.now(),
            created_by=created_by,
            option=new_option,
        )
        s.add(user)
        logging.info(f"Created user {email} id={user.id} by {created_by}")
        return user

    return run_in_session(logic, commit=True)


def get_user_by_id(user_id: int) -> Optional[User]:
    return run_in_session(
        lambda s: s.query(User).filter(User.id == user_id).one_or_none()
    )


def get_user_by_email(email: str) -> Optional[User]:
    return run_in_session(
        lambda s: s.query(User).filter(User.email == email).one_or_none()
    )


def get_users_created_by(user_id: int) -> List[User]:
    return run_in_session(
        lambda s: s.query(User).filter(User.created_by == user_id).all(), default=[]
    )


def update_user(user_id: int, **kwargs) -> Optional[User]:

    def logic(s: Session) -> Optional[User]:
        user = s.query(User).filter(User.id == user_id).one_or_none()
        if not user:
            logging.warning(f"User id={user_id} not found for update")
            return None
        for k, v in kwargs.items():
            if hasattr(user, k):
                setattr(user, k, v)
        logging.info(f"Updated user id={user_id}: {list(kwargs.keys())}")
        return user

    return run_in_session(logic, commit=True)


def delete_user(user_id: int) -> bool:
    def logic(s):
        user = s.query(User).filter(User.id == user_id).one_or_none()
        if not user:
            logging.warning(f"User id={user_id} not found for deletion")
            return False
        s.delete(user)
        logging.info(f"Deleted user id={user_id}")
        return True

    return run_in_session(logic, commit=True, default=False)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), hashed_password.encode("utf-8")
        )
    except Exception as e:
        logging.error(f"Password verification failed: {e}")
        return False
