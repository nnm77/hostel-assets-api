from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


# ── Auth ──────────────────────────────────────────────────────────────────────

class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)


class UserLogin(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ── Category ──────────────────────────────────────────────────────────────────

class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class CategoryResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ── Product ───────────────────────────────────────────────────────────────────

class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    price: float = Field(..., ge=0)
    sku: str = Field(..., min_length=1, max_length=50)
    image: Optional[str] = None
    quantity: int = Field(default=0, ge=0)
    category_id: Optional[int] = None
    low_stock_threshold: int = Field(default=10, ge=0)

    @field_validator("price")
    @classmethod
    def price_precision(cls, v: float) -> float:
        return round(v, 2)


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    price: Optional[float] = Field(None, ge=0)
    image: Optional[str] = None
    quantity: Optional[int] = Field(None, ge=0)
    category_id: Optional[int] = None
    low_stock_threshold: Optional[int] = Field(None, ge=0)

    @field_validator("price")
    @classmethod
    def price_precision(cls, v: Optional[float]) -> Optional[float]:
        return round(v, 2) if v is not None else v


class ProductResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    price: float
    sku: str
    image: Optional[str]
    quantity: int
    low_stock_threshold: int
    is_low_stock: bool
    category_id: Optional[int]
    category: Optional[CategoryResponse]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ── Pagination ────────────────────────────────────────────────────────────────

class PaginatedProducts(BaseModel):
    total: int
    page: int
    page_size: int
    pages: int
    items: List[ProductResponse]


# ── Stock Alert ───────────────────────────────────────────────────────────────

class StockAlert(BaseModel):
    id: int
    name: str
    sku: str
    quantity: int
    low_stock_threshold: int
