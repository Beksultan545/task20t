import redis.asyncio as redis
from config import settings  # .env-тен конфигурация

# Redis URL-ды .env арқылы жинаймыз
REDIS_URL = f"redis://{settings.redis_host}:{settings.redis_port}"

# Redis клиент
redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)

# FastAPI Depends үшін функция
async def get_redis():
    return redis_client
