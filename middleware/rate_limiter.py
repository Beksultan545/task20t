from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from fastapi import Request
from redis import asyncio as aioredis
from config import settings
import logging

logger = logging.getLogger(__name__)

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
            path = request.url.path
            client_ip = request.client.host or "unknown"

            # /metrics және /health секілді жүйелік жолдар үшін шектеу қолданылмайды
            if path.startswith("/metrics") or path.startswith("/health"):
                return await call_next(request)

            key = f"ratelimit:{client_ip}:{path}"
            limit = settings.rate_limit             # мыс: 10
            window = settings.rate_limit_window     # мыс: 60 секунд

            current = await self.redis.incr(key)
            if current == 1:
                await self.redis.expire(key, window)

            if current > limit:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Сұраныс шегі асқан. Кейінірек қайталап көріңіз."}
                )

        except Exception as e:
            logger.warning(f"[RateLimiter] Redis қате: {e}")
            # Redis істемесе, қолданушыны бұғаттамаймыз

        return await call_next(request)
