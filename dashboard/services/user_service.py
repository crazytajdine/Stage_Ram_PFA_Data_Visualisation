# services/user_service.py
from typing import Optional
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from data_managers.database_manager import get_engine
from schemas.database_models import User
import bcrypt
import logging

SessionLocal = sessionmaker(bind=None)


def get_session():
    engine = get_engine()
    if engine is None:
        raise Exception("Database engine not available")
    SessionLocal.configure(bind=engine)
    return SessionLocal()


@contextmanager
def session_scope():
    session = get_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def create_user(email: str, password: str, role_id: int) -> User:
    with session_scope() as session:
        hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        user = User(email=email, password=hashed_pw, role_id=role_id)
        session.add(user)
        session.refresh(user)
        return user


def get_user_by_email(email: str) -> Optional[User]:
    with session_scope() as session:
        user = session.query(User).filter_by(email=email).first()
        return user


def authenticate_user(email: str, password: str) -> Optional[User]:
    user = get_user_by_email(email)
    if user and bcrypt.checkpw(password.encode(), user.password.encode()):
        return user
    return None
