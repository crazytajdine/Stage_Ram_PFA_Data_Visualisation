from typing import Optional
from services import session_service
from data_managers.database_manager import session_scope


def validate_session(token: str) -> Optional[int]:
    if not token:
        return None

    with session_scope(False) as session:
        return session_service.validate_session(token, session)
