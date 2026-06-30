from fastapi import APIRouter, Depends, status
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
async def create_room(body: RoomCreate,_: int = Depends(get_current_user)):

    """Create a new room."""
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