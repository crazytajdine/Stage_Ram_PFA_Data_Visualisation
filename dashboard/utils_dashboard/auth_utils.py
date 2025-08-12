# dashboard/utils_dashboard/auth_utils.py
from typing import Optional, Dict, Any
from schemas.auth import UserSession        # your pydantic model
from dashboard.state import session_manager  # shared singleton

def get_session(session_data: Optional[Dict[str, Any]]) -> Optional[UserSession]:
    """Return the live session object or None if missing/expired."""
    sid = session_data.get("session_id") if session_data else None
    if not sid:
        return None
    return session_manager.get_session(sid)

def is_authenticated(session_data: Optional[Dict[str, Any]]) -> bool:
    return get_session(session_data) is not None

def user_role(session_data: Optional[Dict[str, Any]]) -> Optional[str]:
    sess = get_session(session_data)
    return sess.role if sess else None

def user_email(session_data: Optional[Dict[str, Any]]) -> Optional[str]:
    sess = get_session(session_data)
    return sess.email if sess else None
