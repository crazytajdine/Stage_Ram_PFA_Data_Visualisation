from datetime import datetime
from typing import Optional, Dict, Any
import logging
from schemas.database_models import Option
from data_managers.database_manager import run_in_session
from sqlalchemy.orm import Session


def create_options(user_id: int, preferences: Dict[str, Any]) -> Optional[Option]:

    def logic(s: Session) -> Optional[Option]:
        options = Option(
            user_id=user_id,
            preferences=preferences,
            updated_at=datetime.now(),
        )
        s.add(options)
        logging.info(f"Created options for user {user_id}")
        return options

    return run_in_session(logic, commit=True)


def get_options_by_user(user_id: int) -> Optional[Option]:
    return run_in_session(
        lambda s: s.query(Option).filter(Option.user_id == user_id).one_or_none()
    )


def update_options(user_id: int, new_preferences: Dict[str, Any]) -> Optional[Option]:
    def logic(s: Session) -> Optional[Option]:
        options = s.query(Option).filter(Option.user_id == user_id).one_or_none()
        if options is None:
            logging.warning(
                f"User {user_id} tried to update options for user {user_id}, but none found"
            )
            return None
        options.preferences = new_preferences
        logging.info(f"User {user_id} updated options for user {user_id}")
        return options

    return run_in_session(logic, commit=True)
