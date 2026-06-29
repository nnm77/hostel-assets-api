from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.core.database import prisma
from app.core.security import get_current_user
from app.models.schemas import HostelCreateCreate, HostelResponseResponse

router = APIRouter()


@router.get("/", response_model=List[HostelResponse])
async def list_hostels(_: int = Depends(get_current_user)):
    """List all hostels."""
    return await prisma.category.find_many(order={"name": "asc"})


@router.post("/", response_model=HostelResponse, status_code=status.HTTP_201_CREATED)
async def create_hostel(body: CategoryCreate, _: int = Depends(get_current_user)):
    """Create a new hostel."""
    existing = await prisma.category.find_first(where={"name": body.name})
    if existing:
        raise HTTPException(status_code=400, detail="Category name already exists")
    return await prisma.category.create(data={"name": body.name, "description": body.description})


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_hostel(category_id: int, _: int = Depends(get_current_user)):
    """Delete a hostel (products keep their data, category_id becomes null)."""
    existing = await prisma.category.find_unique(where={"id": category_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Category not found")
    await prisma.category.delete(where={"id": category_id})
