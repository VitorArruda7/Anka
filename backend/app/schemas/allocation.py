from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class AllocationBase(BaseModel):
    client_id: int
    asset_id: int
    quantity: Decimal
    buy_price: Decimal
    buy_date: date


class AllocationCreate(AllocationBase):
    pass


class AllocationRead(AllocationBase):
    id: int

    model_config = {"from_attributes": True}
