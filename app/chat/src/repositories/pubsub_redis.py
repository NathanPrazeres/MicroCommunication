import config
import redis.asyncio as redis
import logging

logger = logging.getLogger(__name__)


def _redis_port() -> int:
    try:
        return int(config.REDIS_PORT)
    except (TypeError, ValueError):
        logger.warning("Invalid REDIS_PORT config, defaulting to 6379")
        return 6379

logger.info("Connecting to Redis at %s:%d", config.REDIS_HOST, _redis_port())
redis_client = redis.Redis(
    host=config.REDIS_HOST,
    port=_redis_port(),
    decode_responses=True
)
logger.info("Redis client initialized")
