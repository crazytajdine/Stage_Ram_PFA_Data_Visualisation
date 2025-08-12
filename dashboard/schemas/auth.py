# dashboard/schemas/auth.py
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    """Payload used by Admin UI to create a user."""
    email: EmailStr
    password: str
    # free-form role (e.g., "admin", "ops", "analyst"); lowercase normalized
    role: str = Field(min_length=1)

    @field_validator("role")
    @classmethod
    def _normalize_role(cls, v: str) -> str:
        v = (v or "").strip().lower()
        if not v:
            raise ValueError("role cannot be empty")
        return v


class UserLogin(BaseModel):
    """Payload posted by the login form."""
    email: EmailStr
    password: str


class UserSession(BaseModel):
    """
    Session object stored server-side (Redis/in-memory) and mirrored (lightly)
    client-side via dcc.Store. `permissions` is a list of page slugs the user
    can access (e.g., ["dashboard","analytics"]). If None → all pages allowed.
    """
    email: EmailStr
    role: str
    login_time: datetime
    session_id: str
    permissions: Optional[List[str]] = None  # page slugs; None = all pages

    @field_validator("role")
    @classmethod
    def _normalize_role(cls, v: str) -> str:
        v = (v or "").strip().lower()
        if not v:
            raise ValueError("role cannot be empty")
        return v

    @field_validator("permissions", mode="after")
    @classmethod
    def _normalize_slugs(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is None:
            return None
        # ensure slug format: no leading "/", no blanks, lowercase
        norm = []
        for s in v:
            if not s:
                continue
            slug = s.strip().lstrip("/").lower()
            if slug:
                norm.append(slug)
        return norm


class UserInfo(BaseModel):
    """Row returned from the users table for display/admin."""
    id: int
    email: EmailStr
    role: str
    created_at: datetime
    created_by: Optional[str] = None
    is_active: bool

    @field_validator("role")
    @classmethod
    def _normalize_role(cls, v: str) -> str:
        return (v or "").strip().lower()


# Optional helper schemas for the Admin permissions UI/APIs

class RolePermissions(BaseModel):
    """Assign allowed pages to a role."""
    role: str
    pages: List[str]  # page slugs

    @field_validator("role")
    @classmethod
    def _normalize_role(cls, v: str) -> str:
        v = (v or "").strip().lower()
        if not v:
            raise ValueError("role cannot be empty")
        return v

    @field_validator("pages", mode="after")
    @classmethod
    def _normalize_pages(cls, v: List[str]) -> List[str]:
        return [p.strip().lstrip("/").lower() for p in v if p and p.strip()]


class UserPermissions(BaseModel):
    """Optional per-user override of allowed pages."""
    email: EmailStr
    pages: List[str]

    @field_validator("pages", mode="after")
    @classmethod
    def _normalize_pages(cls, v: List[str]) -> List[str]:
        return [p.strip().lstrip("/").lower() for p in v if p and p.strip()]
