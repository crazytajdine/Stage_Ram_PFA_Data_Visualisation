from datetime import datetime
from typing import Optional
import uuid
import logging
from data_managers.database_manager import run_in_session
from schemas.database_models import Session
import sqlalchemy.orm as sa_orm


def create_session(user_id: int, expires_at: datetime) -> Optional[Session]:

    def logic(s: sa_orm.Session) -> Optional[Session]:
        new_session = Session(
            id=str(uuid.uuid4()),
            user_id=user_id,
            expires_at=expires_at,
            created_at=datetime.now(),
        )
        s.add(new_session)
        logging.info(f"Created new session {new_session.id} for user {user_id}")
        return new_session

    return run_in_session(logic, commit=True)


def get_session_by_id(session_id: str) -> Optional[Session]:
    return run_in_session(
        lambda s: s.query(Session).filter(Session.id == session_id).one_or_none()
    )


def get_sessions_by_user(user_id: int) -> list[Session]:
    return run_in_session(
        lambda s: s.query(Session).filter(Session.user_id == user_id).all(), default=[]
    )


def delete_session(session_id: str) -> bool:

    def logic(s: sa_orm.Session) -> bool:
        sess = s.query(Session).filter(Session.id == session_id).one_or_none()
        if not sess:
            logging.warning(f"Cannot delete; session {session_id} not found")
            return False
        s.delete(sess)
        logging.info(f"Deleted session {session_id}")
        return True

    return run_in_session(logic, commit=True, default=False)


def get_active_sessions(user_id: int) -> list[Session]:
    now = datetime.now()
    return run_in_session(
        lambda s: s.query(Session)
        .filter(Session.user_id == user_id, Session.expires_at > now)
        .all(),
        default=[],
    )
