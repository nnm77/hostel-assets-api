import math
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status

from app.core.database import prisma
from app.core.queue import push_to_queue
from app.core.security import get_current_user
from app.models.schemas import (
    PaginatedProducts,
    ProductCreate,
    ProductResponse,
    ProductUpdate,
    StockAlert,
)

router = APIRouter()


def _to_response(product) -> dict:
    """Convert a Prisma product record to a dict compatible with ProductResponse."""
    return {
        **product.__dict__,
        "is_low_stock": product.quantity <= product.low_stock_threshold,
        "category": product.category if hasattr(product, "category") else None,
    }


@router.get("/", response_model=PaginatedProducts)
async def list_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, description="Filter by name or description"),
    category_id: Optional[int] = Query(None),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    #changed authentication ,
    _: int = None,
):
    """
    Paginated, filtered product listing.

    Supports search by name/description, category, price range, and date range.
    """
    where: dict = {}

    if search:
        where["OR"] = [
            {"name": {"contains": search}},
            {"description": {"contains": search}},
        ]
    if category_id is not None:
        where["category_id"] = category_id
    if min_price is not None:
        where.setdefault("price", {})["gte"] = min_price
    if max_price is not None:
        where.setdefault("price", {})["lte"] = max_price
    if start_date:
        where.setdefault("created_at", {})["gte"] = start_date
    if end_date:
        where.setdefault("created_at", {})["lte"] = end_date

    skip = (page - 1) * page_size
    total = await prisma.product.count(where=where)
    products = await prisma.product.find_many(
        where=where,
        skip=skip,
        take=page_size,
        order={"created_at": "desc"},
        include={"category": True},
    )

    return PaginatedProducts(
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total else 0,
        items=[_to_response(p) for p in products],
    )


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    body: ProductCreate,
    background_tasks: BackgroundTasks,
    #changed authentication,
    _: int = None,
):
    """Create a new product. Queues it for async background processing."""
    existing = await prisma.product.find_first(where={"sku": body.sku})
    if existing:
        raise HTTPException(status_code=400, detail=f"SKU '{body.sku}' already exists")

    if body.category_id is not None:
        cat = await prisma.category.find_unique(where={"id": body.category_id})
        if not cat:
            raise HTTPException(status_code=404, detail="Category not found")

    product = await prisma.product.create(
        data={
            "name": body.name,
            "description": body.description,
            "price": body.price,
            "sku": body.sku,
            "image": body.image,
            "quantity": body.quantity,
            "low_stock_threshold": body.low_stock_threshold,
            "category_id": body.category_id,
        },
        include={"category": True},
    )
    background_tasks.add_task(push_to_queue, product.id)
    return _to_response(product)


@router.get("/low-stock", response_model=List[StockAlert])
#changed depeneds(get_currecnt_user) to none
async def low_stock_alerts(_: int = Depends(get_current_user)):
    """
    Returns all products where quantity is at or below their low_stock_threshold.
    Use this endpoint to power reorder alerts or dashboard warnings.
    """
    products = await prisma.query_raw(
        "SELECT id, name, sku, quantity, low_stock_threshold "
        "FROM Product "
        "WHERE quantity <= low_stock_threshold "
        "ORDER BY quantity ASC"
    )
    return products


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: int, _: int = Depends(get_current_user)):
    """Retrieve a single product by ID."""
    product = await prisma.product.find_unique(
        where={"id": product_id}, include={"category": True}
    )
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return _to_response(product)


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    body: ProductUpdate,
    #changed authentication
    _: int = None
):
    """Partially update a product. Only provided fields are changed."""
    existing = await prisma.product.find_unique(where={"id": product_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Product not found")

    if body.category_id is not None:
        cat = await prisma.category.find_unique(where={"id": body.category_id})
        if not cat:
            raise HTTPException(status_code=404, detail="Category not found")

    data = body.model_dump(exclude_unset=True)
    updated = await prisma.product.update(
        where={"id": product_id}, data=data, include={"category": True}
    )
    return _to_response(updated)


@router.patch("/{product_id}/stock", response_model=ProductResponse)
async def adjust_stock(
    product_id: int,
    delta: int = Query(..., description="Positive to add stock, negative to remove"),
    #changed authentication
    _: int = None
):
    """
    Adjust stock quantity by a delta value.
    E.g. delta=50 adds 50 units; delta=-10 removes 10 units.
    """
    existing = await prisma.product.find_unique(where={"id": product_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Product not found")

    new_qty = existing.quantity + delta
    if new_qty < 0:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient stock. Current: {existing.quantity}, delta: {delta}",
        )

    updated = await prisma.product.update(
        where={"id": product_id},
        data={"quantity": new_qty},
        include={"category": True},
    )
    return _to_response(updated)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(product_id: int, _: int = Depends(get_current_user)):
    """Permanently delete a product."""
    existing = await prisma.product.find_unique(where={"id": product_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Product not found")
    await prisma.product.delete(where={"id": product_id})
