import math
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status

from app.core.database import prisma
from app.core.queue import push_to_queue
from app.core.security import get_current_user
from app.models.schemas import (
    PaginatedAssets,
    AssetCreate,
    AssetResponse,
    AssetUpdate,
)

router = APIRouter()



@router.get("/", response_model=PaginatedAssets)
async def list_assets(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    _: int = Depends(get_current_user),
):
    """List all assets with optional search."""

    where = {}

    if search:
        where["OR"] = [
            {"name": {"contains": search}},
            {"description": {"contains": search}},
        ]

    skip = (page - 1) * page_size

    total = await prisma.asset.count(where=where)

    assets = await prisma.asset.find_many(
        where=where,
        skip=skip,
        take=page_size,
        order={"created_at": "desc"},
    )

    return PaginatedAssets(
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total else 0,
        items=assets,
    )


@router.post("/", response_model=AssetResponse, status_code=status.HTTP_201_CREATED)
async def create_asset(
    body: AssetCreate,
    background_tasks: BackgroundTasks,
    _: int = Depends(get_current_user),
):
    """Create a new asset."""

    room = await prisma.room.find_unique(where={"id": body.room_id})
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    

    asset = await prisma.asset.create(
        data={
            "name": body.name,
            "description": body.description,
            "asset_type": body.asset_type,
            "condition": body.condition,
            "image": body.image,
            "quantity": body.quantity,
            "room_id": body.room_id,
        }
    )

    background_tasks.add_task(push_to_queue, asset.id)
    return asset



@router.get("/{asset_id}", response_model=AssetResponse)
async def get_asset(asset_id: int, _: int = Depends(get_current_user)):
    """Retrieve an asset by ID."""

    asset = await prisma.asset.find_unique(where={"id": asset_id})

    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    return asset

@router.put("/{asset_id}", response_model=AssetResponse)
async def update_asset(
    asset_id: int,
    body: AssetUpdate,
    _: int = Depends(get_current_user),
):
    """Update an asset."""

    existing = await prisma.asset.find_unique(where={"id": asset_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Asset not found")

    if body.room_id is not None:
        room = await prisma.room.find_unique(where={"id": body.room_id})
        if not room:
            raise HTTPException(status_code=404, detail="Room not found")

    data = body.model_dump(exclude_unset=True)

    updated = await prisma.asset.update(
        where={"id": asset_id},
        data=data,
    )

    return updated


@router.patch("/{asset_id}/quantity", response_model=AssetResponse)
async def adjust_quantity(
    asset_id: int,
    delta: int = Query(..., description="Positive to add, negative to remove"),
    _: int = Depends(get_current_user),
):
    """Adjust asset quantity."""

    asset = await prisma.asset.find_unique(where={"id": asset_id})
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    new_quantity = asset.quantity + delta

    if new_quantity < 0:
        raise HTTPException(
            status_code=400,
            detail="Quantity cannot be negative",
        )

    updated = await prisma.asset.update(
        where={"id": asset_id},
        data={"quantity": new_quantity},
    )

    return updated

@router.delete("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_asset(
    asset_id: int,
    _: int = Depends(get_current_user),
):
    """Delete an asset."""

    existing = await prisma.asset.find_unique(where={"id": asset_id})

    if not existing:
        raise HTTPException(status_code=404, detail="Asset not found")

    await prisma.asset.delete(where={"id": asset_id})