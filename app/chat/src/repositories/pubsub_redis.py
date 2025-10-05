import redis.asyncio as redis

# TODO: review host
redis_client = redis.Redis(
    host="redis.local",
    port=6379,
    decode_responses=True
)
