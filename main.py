from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.database import prisma
from app.routers import assets, auth, categories, rooms
from app.core.queue import start_queue_consumer, stop_queue_consumer


@asynccontextmanager
async def lifespan(app: FastAPI):
    await prisma.connect()
    await start_queue_consumer()
    yield
    await stop_queue_consumer()
    await prisma.disconnect()


app = FastAPI(
    title="Hostel Asset Management API",
    version="2.0.0",
    description=(
    "Backend API for managing hostels, rooms, assets and maintenance requests "
    "using FastAPI, Prisma ORM, JWT authentication and SQLite."
    ),
    lifespan=lifespan,
    redoc_url="/redoc",
)

app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(assets.router, prefix="/assets", tags=["Assets"])
app.include_router(categories.router, prefix="/hostels", tags=["Hostels"])
app.include_router(rooms.router, prefix="/rooms", tags=["Rooms"])


@app.get("/", tags=["Health"])
def home():
    """Health check — visit /docs for the full API."""
    return {"status": "ok", "docs": "/docs"}
