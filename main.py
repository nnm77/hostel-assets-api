from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.database import prisma
from app.routers import products, auth, categories
from app.core.queue import start_queue_consumer, stop_queue_consumer


@asynccontextmanager
async def lifespan(app: FastAPI):
    await prisma.connect()
    await start_queue_consumer()
    yield
    await stop_queue_consumer()
    await prisma.disconnect()


app = FastAPI(
    title="Inventory Manager API",
    version="2.0.0",
    description=(
        "Production-ready Inventory Management System with JWT auth, "
        "categories, stock alerts, pagination, and async background processing."
    ),
    lifespan=lifespan,
    redoc_url="/redoc",
)

app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(products.router, prefix="/products", tags=["Products"])
app.include_router(categories.router, prefix="/categories", tags=["Categories"])


@app.get("/", tags=["Health"])
def home():
    """Health check — visit /docs for the full API."""
    return {"status": "ok", "docs": "/docs"}
