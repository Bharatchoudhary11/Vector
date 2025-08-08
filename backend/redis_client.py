import asyncio
import os
import redis.asyncio as redis
from kombu.utils.url import safequote

redis_host = safequote(os.environ.get('REDIS_HOST', 'localhost'))
redis_client = redis.Redis(host=redis_host, port=6379, db=0)

# In-memory fallback if Redis is unavailable
_local_store: dict[str, str] = {}


async def add_key_value_redis(key, value, expire: int | None = None):
    """Store a value in Redis or fall back to local memory."""
    try:
        await redis_client.set(key, value)
        if expire:
            await redis_client.expire(key, expire)
    except redis.exceptions.ConnectionError:
        _local_store[key] = value
        if expire:
            loop = asyncio.get_running_loop()
            loop.call_later(expire, _local_store.pop, key, None)


async def get_value_redis(key):
    """Retrieve a value from Redis or local memory."""
    try:
        return await redis_client.get(key)
    except redis.exceptions.ConnectionError:
        return _local_store.get(key)


async def delete_key_redis(key):
    """Remove a key from Redis or local memory."""
    try:
        await redis_client.delete(key)
    except redis.exceptions.ConnectionError:
        _local_store.pop(key, None)
