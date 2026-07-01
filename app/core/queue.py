"""
Future feature:
Background task queue for maintenance notifications,
scheduled inspections, or report generation.
Currently not integrated.
"""





import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import Optional

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
QUEUE_KEY = "inventory:product_queue"

_consumer_task: Optional[asyncio.Task] = None
_redis = None


async def _get_redis():
    """Lazily connect to Redis; returns None if Redis is unavailable."""
    global _redis
    if _redis is not None:
        return _redis
    try:
        import aioredis  # type: ignore
        _redis = await aioredis.create_redis_pool(REDIS_URL)
        logger.info("Redis connected at %s", REDIS_URL)
        return _redis
    except Exception as exc:
        logger.warning("Redis unavailable (%s) — queue disabled", exc)
        return None


async def push_to_queue(product_id: int) -> None:
    """Push a product ID onto the processing queue."""
    redis = await _get_redis()
    if redis is None:
        return
    try:
        await redis.lpush(QUEUE_KEY, str(product_id))
        logger.debug("Queued product %s", product_id)
    except Exception as exc:
        logger.error("Queue push failed: %s", exc)


async def _consume_loop() -> None:
    """Background loop that drains the product queue."""
    logger.info("Queue consumer started")
    while True:
        redis = await _get_redis()
        if redis is None:
            await asyncio.sleep(10)
            continue
        try:
            result = await redis.brpop(QUEUE_KEY, timeout=5)
            if result:
                _, raw = result
                product_id = int(raw)
                logger.info("Processing queued product id=%s", product_id)
                # ── pluging in real processing logic here ──
        except asyncio.CancelledError:
            logger.info("Queue consumer stopping")
            raise
        except Exception as exc:
            logger.error("Queue consumer error: %s", exc)
            await asyncio.sleep(2)


async def start_queue_consumer() -> None:
    global _consumer_task
    _consumer_task = asyncio.create_task(_consume_loop())


async def stop_queue_consumer() -> None:
    global _consumer_task, _redis
    if _consumer_task:
        _consumer_task.cancel()
        try:
            await _consumer_task
        except asyncio.CancelledError:
            pass
    if _redis:
        _redis.close()
        await _redis.wait_closed()
        _redis = None
