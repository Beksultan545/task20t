from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from fastapi import Request
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

            # /metrics секілді жүйелік URL-дардан шығамыз
            if path.startswith("/metrics"):
                return await call_next(request)

            key = f"ratelimit:{client_ip}:{path}"
            ttl = settings.rate_limit_window
            limit = settings.rate_limit

            current = await self.redis.incr(key)
            if current == 1:
                await self.redis.expire(key, ttl)

            if current > limit:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Сұраныс шегі асқан. Кейінірек қайталап көріңіз."}
                )

        except Exception as e:
            print(f"[RateLimiter] Redis error: {e}")
            # Redis істемей қалса, бәрібір сұранысты өткіземіз

        return await call_next(request)
