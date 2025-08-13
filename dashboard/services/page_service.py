from typing import Optional
import logging
from sqlalchemy.orm import Session
from schemas.database_models import Page


def create_page(
    page_name: str, session: Session, created_by: Optional[int] = None
) -> Page:
    page = Page(
        page_name=page_name,
    )
    session.add(page)
    session.flush()
    logging.info(f"Page '{page_name}' created by user {created_by}")
    return page


def get_page_by_id(page_id: int, session: Session) -> Optional[Page]:
    return session.query(Page).filter(Page.id == page_id).one_or_none()


def get_page_by_name(page_name: str, session: Session) -> Optional[Page]:
    return session.query(Page).filter(Page.page_name == page_name).one_or_none()


def update_page(
    page_id: int, new_name: str, performed_by: int, session: Session
) -> Optional[Page]:
    page = session.query(Page).filter(Page.id == page_id).one_or_none()
    if not page:
        logging.warning(
            f"User {performed_by} attempted to update page id={page_id}, but page not found"
        )
        return None
    old_name = page.page_name
    page.page_name = new_name
    logging.info(
        f"User {performed_by} updated page id={page_id} from '{old_name}' to '{new_name}'"
    )
    return page


def delete_page(page_id: int, performed_by: int, session: Session) -> bool:
    page = session.query(Page).filter(Page.id == page_id).one_or_none()
    if not page:
        logging.warning(
            f"User {performed_by} attempted to delete page id={page_id}, but page not found"
        )
        return False
    session.delete(page)
    logging.info(f"User {performed_by} deleted page id={page_id}")
    return True
