from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


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


# ── Hostel──────────────────────────────────────────────────────────────────

class HostelCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class HostelResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ── Asset ───────────────────────────────────────────────────────────────────

class AssetCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None

    asset_type: str = Field(..., min_length=1, max_length=100)
    condition: str = Field(default="Good")

    image: Optional[str] = None
    quantity: int = Field(default=0, ge=0)

    room_id: int

    

class AssetUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None

    asset_type: Optional[str] = Field(None, min_length=1, max_length=100)
    condition: Optional[str] = None

    image: Optional[str] = None
    quantity: Optional[int] = Field(None, ge=0)

    room_id: Optional[int] = None

   

class AssetResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]

    asset_type: str
    condition: str

    image: Optional[str]
    quantity: int

    room_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ── Pagination ────────────────────────────────────────────────────────────────

class PaginatedAssets(BaseModel):
    total: int
    page: int
    page_size: int
    pages: int
    items: List[AssetResponse]



 # ── Room ─────────────────────────────────────────────────────────────────────

class RoomCreate(BaseModel):
    room_number: str = Field(..., min_length=1, max_length=20)
    floor: int
    capacity: int = Field(..., ge=1)
    hostel_id: int


class RoomResponse(BaseModel):
    id: int
    room_number: str
    floor: int
    capacity: int
    hostel_id: int
    created_at: datetime

    class Config:
        from_attributes = True
