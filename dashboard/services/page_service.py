from typing import List, Optional
import logging
from sqlalchemy import Row, case, update
from sqlalchemy.orm import Session
from schemas.database_models import Page, User, role_page_table


def create_page(page_id: str, session: Session) -> Page:
    page = Page(
        id=page_id,
    )
    session.add(page)
    session.flush()
    logging.info(f"Page '{page.id}' created")
    return page


def create_pages(page_ids: List[int], session: Session) -> List[Page]:
    # new_pages = [Page(id=pid) for pid in page_ids if pid not in page_ids]

    # session.bulk_save_objects(new_pages)

    # session.flush()
    new_pages = [create_page(id, session) for id in page_ids]
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


def get_user_allowed_pages_with_preferences(
    user_id: int, session: Session
) -> list[Row]:
    return (
        session.query(role_page_table)
        .join(User, User.role_id == role_page_table.c.role_id)
        .filter(User.id == user_id, role_page_table.c.disabled.is_(False))
        .all()
    )


def get_user_allowed_pages_all(user_id: int, session: Session) -> list[Row]:
    return (
        session.query(role_page_table)
        .join(User, User.role_id == role_page_table.c.role_id)
        .filter(User.id == user_id)
        .all()
    )


def update_user_page_preferences(
    user_id: int, preferences: dict[int, bool], session: Session
) -> bool:
    if not preferences:
        return False

    case_stmt = case(
        preferences,
        value=role_page_table.c.page_id,
    )

    stmt = (
        update(role_page_table)
        .where(role_page_table.c.role_id == User.role_id)
        .where(User.id == user_id)
        .values(disabled=case_stmt)
    )

    session.execute(stmt)
    session.commit()

    return True
