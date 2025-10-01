from __future__ import annotations

import json
import logging
from functools import lru_cache
from typing import Any

from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.core.config import get_settings

logger = logging.getLogger(__name__)


@lru_cache()
def get_redis_client() -> Redis:
    settings = get_settings()
    return Redis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)


async def redis_get_json(key: str) -> Any | None:
    client = get_redis_client()
    try:
        value = await client.get(key)
    except RedisError as exc:
        logger.warning("Redis get failed for %s: %s", key, exc)
        return None
    if value is None:
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError as exc:
        logger.warning("Redis cached value for %s is not valid JSON: %s", key, exc)
        return None


async def redis_set_json(key: str, value: Any, ttl: int | None = None) -> None:
    try:
        payload = json.dumps(value)
    except (TypeError, ValueError) as exc:
        logger.warning("Could not serialize value for %s: %s", key, exc)
        return
    client = get_redis_client()
    try:
        await client.set(key, payload, ex=ttl)
    except RedisError as exc:
        logger.warning("Redis set failed for %s: %s", key, exc)


async def redis_delete(*keys: str) -> None:
    if not keys:
        return
    client = get_redis_client()
    try:
        await client.delete(*keys)
    except RedisError as exc:
        logger.warning("Redis delete failed for %s: %s", ",".join(keys), exc)
