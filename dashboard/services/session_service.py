from datetime import datetime
from typing import Optional
import uuid
import logging
from schemas.database_models import Session
from data_managers.database_manager import session_scope


def create_session(user_id: int, expires_at: datetime) -> Session:
    with session_scope() as session:
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


def get_session_by_id(session_id: str) -> Optional[Session]:
    with session_scope() as session:
        sess = session.query(Session).filter(Session.id == session_id).one_or_none()
        if sess:
            logging.info(f"Found session {session_id}")
        else:
            logging.warning(f"Session {session_id} not found")
        return sess


def get_sessions_by_user(user_id: int) -> list[Session]:
    with session_scope() as session:
        sessions = session.query(Session).filter(Session.user_id == user_id).all()
        logging.info(f"Found {len(sessions)} sessions for user {user_id}")
        return sessions


def delete_session(session_id: str) -> bool:
    with session_scope() as session:
        sess = session.query(Session).filter(Session.id == session_id).one_or_none()
        if sess is None:
            logging.warning(f"Cannot delete; session {session_id} not found")
            return False
        session.delete(sess)
        logging.info(f"Deleted session {session_id}")
        return True
