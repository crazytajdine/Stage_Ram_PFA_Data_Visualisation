from datetime import datetime
from typing import Optional
from pydantic import BaseModel

from schemas.database_models import User


class UserOut(BaseModel):
    id: int
    email: str
    role_id: int
    disabled: bool
    created_at: datetime
    created_by: Optional[int] = None
    model_config = {"from_attributes": True}


def to_user_out(user: User) -> UserOut:
    return UserOut.model_validate(user)
