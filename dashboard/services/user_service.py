from datetime import datetime
from typing import Optional, List
import logging
import bcrypt
from sqlalchemy.orm import Session
from schemas.database_models import User
from mappers.user_mapper import UserOut, to_user_out


def create_user(
    email: str,
    password: str,
    role_id: int,
    session: Session,
    created_by: Optional[int] = None,
) -> Optional[UserOut]:
    user = User(
        email=email,
        password=password,
        role_id=role_id,
        created_at=datetime.now(),
        created_by=created_by,
    )
    session.add(user)
    session.flush()
    logging.info(f"Created user {email} id={user.id} by {created_by}")
    return to_user_out(user)


def get_user_by_id(user_id: int, session: Session) -> Optional[UserOut]:
    user = session.query(User).filter(User.id == user_id).one_or_none()
    return to_user_out(user) if user else None


def get_user_by_email(email: str, session: Session) -> Optional[UserOut]:
    user = session.query(User).filter(User.email == email).one_or_none()
    return to_user_out(user) if user else None


def get_users_created_by(user_id: int, session: Session) -> List[UserOut]:
    users = session.query(User).filter(User.created_by == user_id).all()
    return [to_user_out(u) for u in users]


def update_user(user_id: int, session: Session, **kwargs) -> Optional[UserOut]:
    user = session.query(User).filter(User.id == user_id).one_or_none()
    if not user:
        logging.warning(f"User id={user_id} not found for update")
        return None
    for k, v in kwargs.items():
        if hasattr(user, k):
            setattr(user, k, v)
    logging.info(f"Updated user id={user_id}: {list(kwargs.keys())}")
    return to_user_out(user)


def delete_user(user_id: int, session: Session) -> bool:
    user = session.query(User).filter(User.id == user_id).one_or_none()
    if not user:
        logging.warning(f"User id={user_id} not found for deletion")
        return False
    session.delete(user)
    logging.info(f"Deleted user id={user_id}")
    return True


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), hashed_password.encode("utf-8")
        )
    except Exception as e:
        logging.error(f"Password verification failed: {e}")
        return False
