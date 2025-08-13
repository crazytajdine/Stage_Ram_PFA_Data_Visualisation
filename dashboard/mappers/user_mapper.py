from pydantic import BaseModel

from schemas.database_models import User


class UserOut(BaseModel):
    id: int
    email: str
    role_id: int
    disabled: bool

    model_config = {"from_attributes": True}


def to_user_out(user: User) -> UserOut:
    return UserOut.model_validate(user)
