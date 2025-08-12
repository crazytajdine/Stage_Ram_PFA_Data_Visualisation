# models.py
from datetime import datetime
import uuid
from sqlalchemy import Column, DateTime, Integer, String, ForeignKey, Table
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.dialects.postgresql import JSONB

Base = declarative_base()

role_page_table = Table(
    "role_page",
    Base.metadata,
    Column("role_id", Integer, ForeignKey("roles.id"), primary_key=True),
    Column("page_id", Integer, ForeignKey("pages.id"), primary_key=True),
)


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    role_name = Column(String, unique=True, nullable=False)

    created_at = Column(DateTime, default=datetime.now)
    created_by = Column(Integer, ForeignKey("users.id"))

    created_by_user = relationship("User", back_populates="created_roles")

    users = relationship("User", back_populates="role")

    pages = relationship("Page", secondary=role_page_table, back_populates="roles")


class Page(Base):
    __tablename__ = "pages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    page_name = Column(String, nullable=False)
    roles = relationship("Role", secondary=role_page_table, back_populates="pages")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"))
    session_id = Column(String, ForeignKey("sessions.id"), nullable=True)

    created_at = Column(DateTime, default=datetime.now)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    created_users = relationship("User", back_populates="creator", remote_side=[id])
    creator = relationship("User", back_populates="created_users")

    created_roles = relationship("Role", back_populates="created_by_user")
    role = relationship("Role", back_populates="users")
    session = relationship(
        "Session", back_populates="user", cascade="all,delete-orphan"
    )


class Session(Base):
    __tablename__ = "sessions"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    user = relationship("User", back_populates="session")


class Options(Base):
    __tablename__ = "options"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    preferences = Column(JSONB, nullable=False, default=dict)

    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    user = relationship("User", back_populates="preferences")
