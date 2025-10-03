import redis

redis_client = redis.StrictRedis(host="redis.local", port=6379, decode_responses=True)
