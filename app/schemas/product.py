from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator


class ProductImageCreateRequest(BaseModel):
    url: HttpUrl
    alt_text: str | None = Field(default=None, max_length=180)
    position: int = Field(default=0, ge=0)
    is_primary: bool = False


class ProductImageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    url: str
    alt_text: str | None
    position: int
    is_primary: bool
    created_at: datetime


class ProductBaseRequest(BaseModel):
    category_id: UUID
    name: str = Field(min_length=1, max_length=180)
    slug: str = Field(min_length=1, max_length=220, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    sku: str = Field(min_length=1, max_length=80)
    description: str = Field(min_length=1, max_length=5000)
    price: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    compare_at_price: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    is_active: bool = True
    images: list[ProductImageCreateRequest] = Field(default_factory=list, max_length=10)

    @model_validator(mode="after")
    def validate_compare_at_price(self) -> "ProductBaseRequest":
        if self.compare_at_price is not None and self.compare_at_price < self.price:
            raise ValueError("compare_at_price must be greater than or equal to price")
        return self


class ProductCreateRequest(ProductBaseRequest):
    pass


class ProductUpdateRequest(ProductBaseRequest):
    pass


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    category_id: UUID
    seller_id: UUID
    name: str
    slug: str
    sku: str
    description: str
    price: Decimal
    compare_at_price: Decimal | None
    currency: str
    is_active: bool
    images: list[ProductImageResponse]
    created_at: datetime
    updated_at: datetime


class ProductListResponse(BaseModel):
    items: list[ProductResponse]
    total: int
    limit: int
    offset: int
