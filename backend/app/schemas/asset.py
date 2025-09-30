from pydantic import BaseModel


class AssetBase(BaseModel):
    ticker: str
    name: str
    exchange: str
    currency: str


class AssetCreate(AssetBase):
    pass


class AssetRead(AssetBase):
    id: int

    model_config = {"from_attributes": True}
