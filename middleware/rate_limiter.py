from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, HTTPException
from redis import asyncio as aioredis
from config import settings

class RateLimiterMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.redis = aioredis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            decode_responses=True
        )

    async def dispatch(self, request: Request, call_next):
        try:
            client_ip = request.client.host or "unknown"
            path = request.url.path
            key = f"ratelimit:{client_ip}:{path}"
            ttl = settings.rate_limit_window
            limit = settings.rate_limit

            current = await self.redis.incr(key)
            if current == 1:
                await self.redis.expire(key, ttl)

            if current > limit:
                raise HTTPException(
                    status_code=429,
                    detail="Сұраныс шегі асқан. Кейінірек қайталап көріңіз."
                )

        except HTTPException:
            raise  # лимит асса, тікелей көтереміз

        except Exception as e:
            print(f"[RateLimiter] Redis error: {e}")  # қосымша лог

        return await call_next(request)
