from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AddressBase(BaseModel):
    address_type: Literal["shipping", "billing"]
    full_name: str = Field(min_length=1, max_length=120)
    phone_number: str = Field(min_length=7, max_length=30)
    line1: str = Field(min_length=1, max_length=255)
    line2: str | None = Field(default=None, max_length=255)
    city: str = Field(min_length=1, max_length=120)
    state: str = Field(min_length=1, max_length=120)
    postal_code: str = Field(min_length=1, max_length=30)
    country: str = Field(default="US", min_length=2, max_length=2)
    is_default: bool = False


class AddressCreateRequest(AddressBase):
    pass


class AddressUpdateRequest(AddressBase):
    pass


class AddressResponse(AddressBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
