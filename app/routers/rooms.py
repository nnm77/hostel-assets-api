from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.core.database import prisma
from app.core.security import get_current_user
from app.models.schemas import RoomCreate, RoomResponse


router = APIRouter()


@router.get("/", response_model=List[RoomResponse])
#async def list_rooms(_: int = Depends(get_current_user)):
async def list_rooms(_: int = Depends(get_current_user)):
    """List all rooms."""
    return await prisma.room.find_many(order={"room_number": "asc"})


@router.post("/", response_model=RoomResponse, status_code=status.HTTP_201_CREATED)
#async def create_room(body: RoomCreate, _: int = Depends(get_current_user)):
async def create_room(body: RoomCreate, _: int = Depends(get_current_user)):

    existing = await prisma.room.find_first(
        where={
            "hostel_id": body.hostel_id,
            "room_number": body.room_number,
        }
    )

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Room number already exists in this hostel",
        )

    return await prisma.room.create(
        data={
            "room_number": body.room_number,
            "floor": body.floor,
            "capacity": body.capacity,
            "hostel": {
                "connect": {
                    "id": body.hostel_id
                }
            },
        }
    )  


    
@router.delete("/{room_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_room(
    room_id: int,
    _: int = Depends(get_current_user),
):
    room = await prisma.room.find_unique(where={"id": room_id})

    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    await prisma.room.delete(where={"id": room_id})