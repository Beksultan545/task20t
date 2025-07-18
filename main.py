from fastapi import FastAPI, Depends, HTTPException, status, APIRouter
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator

from database import async_session, engine
from models import Base, User
from config import settings
from crud import get_user_by_username
from schemas import UserCreate, UserLogin, UserOut
from utils import (
    get_password_hash, verify_password,
    create_access_token, get_current_user, require_role
)
from routes import notes, tasks, ws
from middleware.rate_limiter import RateLimiterMiddleware
from logging_config import configure_logging
from logging_middleware import LoggingMiddleware

import logging
from typing import List

# 🔧 INIT
app = FastAPI(
    title="My Awesome API",
    description="Бұл API Notes, Tasks, Authentication және Admin сияқты функционалдарды ұсынады.",
    version="1.0.0",
    contact={"name": "beka", "email": "kopzhasarbeksultan@icloud.com"},
    license_info={"name": "MIT", "url": "https://opensource.org/licenses/MIT"},
)

# 🔐 Middleware
configure_logging()
app.add_middleware(LoggingMiddleware)
app.add_middleware(RateLimiterMiddleware)

# 📊 Prometheus
instrumentator = Instrumentator()
instrumentator.instrument(app).expose(app)

# 📁 Static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# 📦 Routers
app.include_router(notes.router)
app.include_router(tasks.router)
app.include_router(ws.router)

# ✅ Auth
@app.post("/register", tags=["Authentication"], response_model=UserOut, status_code=201)
async def register(user: UserCreate, db: AsyncSession = Depends(lambda: async_session())):
    hashed_password = get_password_hash(user.password)
    new_user = User(username=user.username, hashed_password=hashed_password, role="user")
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    logging.info("New user registered", extra={"username": user.username})
    return new_user


@app.post("/login", tags=["Authentication"])
async def login(user: UserLogin, db: AsyncSession = Depends(lambda: async_session())):
    db_user = await get_user_by_username(db, user.username)
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        logging.warning("Login failed", extra={"username": user.username})
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(data={"sub": user.username})
    logging.info("User logged in", extra={"username": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


# 👤 User info
@app.get("/users/me", tags=["Users"], response_model=UserOut)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user


# 🔐 Admin-only
@app.get("/admin/users", tags=["Admin"], response_model=List[UserOut])
async def get_all_users(
    db: AsyncSession = Depends(lambda: async_session()),
    current_user: User = Depends(require_role("admin"))
):
    result = await db.execute(select(User))
    return result.scalars().all()


# 🧪 Rate Limit Test
@app.get("/test-limit")
async def test_limit():
    return {"msg": "OK"}


# 📂 DB Init
@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
