from typing import List, Optional
import logging
from sqlalchemy.orm import Session
from schemas.database_models import Page


def create_page(page_id: str, session: Session) -> Page:
    page = Page(
        id=page_id,
    )
    session.add(page)
    session.flush()
    logging.info(f"Page '{page.id}' created")
    return page


def create_pages(page_ids: List[int], session: Session) -> List[Page]:
    new_pages = [Page(id=pid) for pid in page_ids if pid not in page_ids]

    session.bulk_save_objects(new_pages)
    return new_pages


def get_pages(session: Session) -> list[Page]:
    return session.query(Page).all()


def get_pages_by_id(ids: List[int], session: Session) -> List[Page]:
    return session.query(Page).filter(Page.id.in_(ids)).all()


def get_page_by_id(page_id: int, session: Session) -> Optional[Page]:
    return session.query(Page).filter(Page.id == page_id).one_or_none()


def delete_page(page_id: int, session: Session) -> bool:
    page = session.query(Page).filter(Page.id == page_id).one_or_none()
    if not page:
        logging.warning(f"Attempted to delete page id={page_id}, but page not found")
        return False
    session.delete(page)
    logging.info(f"Deleted page id={page_id}")
    return True
