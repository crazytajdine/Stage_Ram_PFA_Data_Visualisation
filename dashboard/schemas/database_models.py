# models.py
from datetime import datetime
import uuid
from sqlalchemy import Column, DateTime, Integer, String, ForeignKey, Table, Boolean
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.dialects.postgresql import JSONB

Base = declarative_base()

role_page_table = Table(
    "role_page",
    Base.metadata,
    Column(
        "role_id", Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True
    ),
    Column(
        "page_id", Integer, ForeignKey("pages.id", ondelete="CASCADE"), primary_key=True
    ),
)


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    role_name = Column(String, unique=True, nullable=False)

    created_at = Column(DateTime, default=datetime.now)
    created_by = Column(
        Integer, ForeignKey("users.id"), nullable=True, name="fk_roles_created_by"
    )

    created_by_user = relationship(
        "User",
        back_populates="created_roles",
        foreign_keys=[created_by],
    )

    users = relationship(
        "User",
        back_populates="role",
        foreign_keys="User.role_id",
    )

    pages = relationship(
        "Page",
        secondary=role_page_table,
        back_populates="roles",
    )


class Page(Base):
    __tablename__ = "pages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    page_name = Column(String, nullable=False, unique=True)

    roles = relationship(
        "Role",
        secondary=role_page_table,
        back_populates="pages",
    )


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    disabled = Column(Boolean, default=False)

    role_id = Column(Integer, ForeignKey("roles.id"), name="fk_users_role_id")

    created_at = Column(DateTime, default=datetime.now)
    created_by = Column(
        Integer, ForeignKey("users.id"), nullable=True, name="fk_users_created_by"
    )

    # self-referential: which users this user created
    created_users = relationship(
        "User",
        back_populates="creator",
        remote_side=[id],
        foreign_keys=[created_by],
    )

    creator = relationship(
        "User",
        back_populates="created_users",
        foreign_keys=[created_by],
    )

    option = relationship(
        "Option",
        back_populates="user",
        uselist=False,
    )

    created_roles = relationship(
        "Role",
        back_populates="created_by_user",
        foreign_keys="Role.created_by",
    )

    role = relationship(
        "Role",
        back_populates="users",
        foreign_keys=[role_id],
        uselist=False,
    )

    session = relationship(
        "Session",
        back_populates="user",
        cascade="all,delete-orphan",
        uselist=False,
    )


class Session(Base):
    __tablename__ = "sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    user = relationship(
        "User",
        back_populates="session",
        foreign_keys=[user_id],
        uselist=False,
    )


class Option(Base):
    __tablename__ = "options"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    preferences = Column(JSONB, nullable=False, default=dict)

    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    user = relationship(
        "User",
        back_populates="option",
        foreign_keys=[user_id],
        uselist=False,
    )
