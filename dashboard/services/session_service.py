from datetime import datetime
from typing import Optional, List
import uuid
import logging
import sqlalchemy.orm as sa_orm
from schemas.database_models import Session


def create_session(
    user_id: int, expires_at: datetime, session: sa_orm.Session
) -> Session:
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
    return session.query(Session).filter(Session.id == session_id).one_or_none()


def get_sessions_by_user(user_id: int, session: sa_orm.Session) -> List[Session]:
    return session.query(Session).filter(Session.user_id == user_id).all()


def delete_session(session_id: str, session: sa_orm.Session) -> bool:
    sess = session.query(Session).filter(Session.id == session_id).one_or_none()
    if not sess:
        logging.warning(f"Cannot delete; session {session_id} not found")
        return False
    session.delete(sess)
    logging.info(f"Deleted session {session_id}")
    return True


def get_active_sessions(user_id: int, session: sa_orm.Session) -> List[Session]:
    now = datetime.now()
    return (
        session.query(Session)
        .filter(Session.user_id == user_id, Session.expires_at > now)
        .all()
    )
