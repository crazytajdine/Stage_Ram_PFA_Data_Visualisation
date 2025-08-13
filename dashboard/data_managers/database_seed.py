# db_seed.py
from sqlalchemy.orm import Session
import logging

from mappers.user_mapper import UserOut
from services import role_service, page_service, user_service
from schemas.database_models import User

import bcrypt


def initialize_database_first_time(session: Session):
    # Only run if no users exist
    if session.query(User).first():
        logging.info("Database already initialized with a user.")
        return

    logging.info("Initializing database with default pages, role, and admin user...")

    # Create admin role safely
    admin_role = role_service.create_role("admin", session=session)

    # Create admin user
    salt = bcrypt.gensalt()

    admin_password = bcrypt.hashpw(b"test", salt)
    admin_user: UserOut = user_service.create_user(
        "admin@ff.com", admin_password, admin_role.id, session
    )
    if not admin_user:
        logging.error("Failed to create admin user.")
        return

    # Create default pages and assign to role
    default_pages = ["Dashboard", "Settings", "Reports", "Users", "Analytics"]
    pages = page_service.create_pages(
        default_pages,
        session,
        admin_user,
    )

    role_service.assign_pages_to_role(admin_role, pages, session)

    logging.info(f"Admin user created: {admin_user.email}")
    logging.info("Database initialization completed.")
