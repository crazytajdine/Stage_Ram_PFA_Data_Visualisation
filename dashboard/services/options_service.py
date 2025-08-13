from datetime import datetime
from typing import Optional, Dict, Any
import logging
from sqlalchemy.orm import Session
from schemas.database_models import Option


def create_options(
    user_id: int, preferences: Dict[str, Any], session: Session
) -> Option:
    options = Option(
        user_id=user_id,
        preferences=preferences,
        updated_at=datetime.now(),
    )
    session.add(options)
    logging.info(f"Created options for user {user_id}")
    return options


def get_options_by_user(user_id: int, session: Session) -> Optional[Option]:
    return session.query(Option).filter(Option.user_id == user_id).one_or_none()


def update_options(
    user_id: int, new_preferences: Dict[str, Any], session: Session
) -> Optional[Option]:
    options = session.query(Option).filter(Option.user_id == user_id).one_or_none()
    if not options:
        logging.warning(f"User {user_id} tried to update options, but none found")
        return None
    options.preferences = new_preferences
    logging.info(f"User {user_id} updated options")
    return options
