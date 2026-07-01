from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.core.database import prisma
from app.core.security import get_current_user
from app.models.schemas import HostelCreate, HostelResponse

router = APIRouter()


@router.get("/", response_model=List[HostelResponse])
#cahnged authentication
async def list_hostels(_: int = Depends(get_current_user)):
    """List all hostels."""
    return await prisma.hostel.find_many(order={"name": "asc"})


@router.post("/", response_model=HostelResponse, status_code=status.HTTP_201_CREATED)
#changed
async def create_hostel(body: HostelCreate, _: int = Depends(get_current_user)):
    """Create a new hostel."""
    existing = await prisma.hostel.find_first(where={"name": body.name})
    if existing:
        raise HTTPException(status_code=400, detail="Hostel name already exists")
    return await prisma.hostel.create(data={"name": body.name, "description": body.description})


@router.delete("/{hostel_id}", status_code=status.HTTP_204_NO_CONTENT)
#changed
async def delete_hostel(hostel_id: int, _: int = Depends(get_current_user)):
    """Delete a hostel."""
    existing = await prisma.hostel.find_unique(where={"id": hostel_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Hostel not found")
    await prisma.hostel.delete(where={"id": hostel_id})
