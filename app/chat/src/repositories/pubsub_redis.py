import config
import redis.asyncio as redis


def _redis_port() -> int:
    try:
        return int(config.REDIS_PORT)
    except (TypeError, ValueError):
        return 6379

redis_client = redis.Redis(
    host=config.REDIS_HOST,
    port=_redis_port(),
    decode_responses=True
)
