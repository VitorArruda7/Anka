from datetime import datetime

from pydantic import BaseModel, EmailStr


class ClientBase(BaseModel):
    name: str
    email: EmailStr
    is_active: bool = True


class ClientCreate(ClientBase):
    pass


class ClientUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    is_active: bool | None = None


class ClientRead(ClientBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}
