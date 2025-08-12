from datetime import datetime
from typing import Optional, Dict, Any
import logging
from schemas.database_models import Option
from data_managers.database_manager import session_scope


def create_options(user_id: int, preferences: Dict[str, Any]) -> Option:
    with session_scope() as session:
        options = Option(
            user_id=user_id,
            preferences=preferences,
            updated_at=datetime.now(),
        )
        session.add(options)
        session.flush()
        logging.info(f"Created options for user {user_id}")
        return options


def get_options_by_user(user_id: int) -> Optional[Option]:
    with session_scope() as session:
        options = session.query(Option).filter(Option.user_id == user_id).one_or_none()
        if options:
            logging.info(f"Retrieved options for user {user_id}")
        else:
            logging.warning(f"No options found for user {user_id}")
        return options


def update_options(user_id: int, new_preferences: Dict[str, Any]) -> Optional[Option]:
    with session_scope() as session:
        options = session.query(Option).filter(Option.user_id == user_id).one_or_none()
        if options is None:
            logging.warning(
                f"User {user_id} tried to update options for user {user_id}, but none found"
            )
            return None
        options.preferences = new_preferences
        logging.info(f"User {user_id} updated options for user {user_id}")
        return options
