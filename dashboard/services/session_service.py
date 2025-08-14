from datetime import datetime, timedelta
from typing import Optional, List
import uuid
import logging
import sqlalchemy.orm as sa_orm
from schemas.database_models import Session
from configurations.config import get_base_config


config = get_base_config()

session_expiration_offset_in_hours = config.get("session", {}).get(
    "session_expiration_offset_in_hours", 24
)


def create_session(user_id: int, session: sa_orm.Session) -> Session:

    expires_at = datetime.now() + timedelta(hours=session_expiration_offset_in_hours)

    is_deleted = delete_session_with_user_id(user_id, session)
    if is_deleted:
        logging.debug(f"Deleted previous session for user {user_id}")

    new_session = Session(
        id=str(uuid.uuid4()),
        user_id=user_id,
        expires_at=expires_at,
        created_at=datetime.now(),
    )
    session.add(new_session)
    session.flush()
    logging.info(f"Created new session {new_session.id} for user {user_id}")
    return new_session


def get_session_by_id(session_id: str, session: sa_orm.Session) -> Optional[Session]:
    return (
        session.query(Session)
        .filter(Session.id == session_id, Session.expires_at > datetime.now())
        .one_or_none()
    )


def get_sessions_by_user(user_id: int, session: sa_orm.Session) -> List[Session]:

    return session.query(Session).filter(Session.user_id == user_id).all()


def delete_session(session_id: str, session: sa_orm.Session) -> bool:
    sess = session.query(Session).filter(Session.id == session_id).one_or_none()
    if not sess:
        logging.warning(f"Cannot delete; session {session_id} not found")
        return False
    session.delete(sess)
    session.flush()
    logging.info(f"Deleted session {session_id}")
    return True


def delete_session_with_user_id(user_id: int, session: sa_orm.Session) -> bool:
    sess = session.query(Session).filter(Session.user_id == user_id).one_or_none()
    if not sess:
        logging.warning(f"Cannot delete; no session found for user {user_id}")
        return False
    session.delete(sess)
    session.flush()
    logging.info(f"Deleted session for user {user_id}")
    return True


def get_active_sessions(user_id: int, session: sa_orm.Session) -> List[Session]:
    now = datetime.now()
    return (
        session.query(Session)
        .filter(Session.user_id == user_id, Session.expires_at > now)
        .all()
    )


def validate_session(token: str, session: sa_orm.Session) -> Optional[int]:
    if not token:
        return None
    sess = get_session_by_id(token, session)
    if not sess:
        return None
    return sess.user_id
