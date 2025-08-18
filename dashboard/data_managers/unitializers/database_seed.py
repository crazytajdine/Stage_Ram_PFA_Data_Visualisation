# db_seed.py
from sqlalchemy.orm import Session
import logging

from services import role_service, page_service, user_service

from utils_dashboard.utils_page import get_all_metadata_id_pages_dynamic
import bcrypt


def initialize_database_first_time(session: Session):
    logging.info("Initializing database...")

    admin_role = role_service.get_role_by_id(0, session)
    if not admin_role:
        admin_role = role_service.create_role(
            "admin", session, is_admin=True, change_file=True, id=0
        )
        logging.info("Admin role created with id=0")
    else:
        logging.info("Admin role already exists")

    # --- 2. Ensure admin user with id=0 exists ---
    admin_user = user_service.get_user_by_id(0, session)
    if not admin_user:
        salt = bcrypt.gensalt()
        admin_password = bcrypt.hashpw("test".encode("utf-8"), salt).decode("utf-8")
        admin_user = user_service.create_user(
            id=0,
            email="admin@ff.com",
            password=admin_password,
            role_id=admin_role.id,
            session=session,
        )
        logging.info("Admin user created with id=0")
    else:
        logging.info("Admin user already exists")

    # --- 3. Ensure default pages exist ---
    default_pages = get_all_metadata_id_pages_dynamic()
    # Fetch existing pages by name
    existing_pages = page_service.get_pages_by_id(default_pages, session)

    existing_ids = {p.id for p in existing_pages}
    # Only create missing pages
    missing_pages = [id for id in default_pages if id not in existing_ids]
    logging.info(f"Missing pages to create: {missing_pages}")
    new_pages = page_service.create_pages(missing_pages, session)

    # Combine all pages
    all_pages = existing_pages + new_pages
    # --- 4. Assign pages to admin role ---
    role_service.assign_pages_to_role(admin_role, all_pages, session)

    logging.info(f"Admin user: {admin_user.email}")
    logging.info("Database initialization completed.")
