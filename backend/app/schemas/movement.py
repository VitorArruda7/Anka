from datetime import date
from decimal import Decimal

from pydantic import BaseModel

from app.models.movement import MovementType


class MovementBase(BaseModel):
    client_id: int
    type: MovementType
    amount: Decimal
    date: date
    note: str | None = None


class MovementCreate(MovementBase):
    pass


class MovementRead(MovementBase):
    id: int

    model_config = {"from_attributes": True}
