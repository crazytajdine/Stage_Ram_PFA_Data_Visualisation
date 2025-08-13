from services import session_service
from data_managers.database_manager import session_scope


def validate_session(token: str) -> bool:
    if not token:
        return False

    with session_scope(False) as session:
        return session_service.validate_session(token, session)
