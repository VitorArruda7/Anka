from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    name: str
    email: EmailStr
    is_active: bool = True


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    is_active: bool | None = None
    password: str | None = None


class UserRead(UserBase):
    id: int
    created_at: datetime

    model_config = {
        "from_attributes": True,
    }
