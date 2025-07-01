import aioredis
from config import settings  # .env-тан конфигурация оқылады

# Redis URL-ды .env арқылы жинаймыз
REDIS_URL = f"redis://{settings.redis_host}:{settings.redis_port}"

# Redis клиент
redis = aioredis.from_url(REDIS_URL, decode_responses=True)

# FastAPI Depends үшін функция
async def get_redis():
    return redis
