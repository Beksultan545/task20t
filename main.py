from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from database import async_session, engine
from models import Base, User
from crud import get_user_by_username
from schemas import UserCreate, UserLogin
from utils import get_password_hash, verify_password, create_access_token, SECRET_KEY, ALGORITHM
from utils import get_current_user, require_role
from sqlalchemy import select
from fastapi.staticfiles import StaticFiles
from config import settings
from prometheus_fastapi_instrumentator import Instrumentator
import schemas, models
from routes import notes, tasks, ws
from fastapi.responses import JSONResponse
from middleware.rate_limiter import RateLimiterMiddleware

# ✅ Logging + Prometheus

from logging_config import configure_logging
from logging_middleware import LoggingMiddleware

import logging

print(settings.database_url)

# ✅ FastAPI init
app = FastAPI(
    title="My Awesome API",
    description="Бұл API Notes, Tasks, Authentication және Admin сияқты функционалдарды ұсынады. Құжаттама толық сипатталған және қолдануға ыңғайлы.",
    version="1.0.0",
    contact={
        "name": "beka",
        "email": "kopzhasarbeksultan@icloud.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    }
)


app.add_middleware(RateLimiterMiddleware)

@app.get("/test-limit")
async def test_limit():
    return {"msg": "OK"}



# ✅ Logging config
configure_logging()
app.add_middleware(LoggingMiddleware)

# ✅ Prometheus
instrumentator = Instrumentator()
instrumentator.instrument(app).expose(app)

# ✅ Static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# ✅ Routers
app.include_router(notes.router)
app.include_router(tasks.router)
app.include_router(ws.router)

# ✅ DB Init
@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# ✅ DB Dependency
async def get_db():
    async with async_session() as session:
        yield session

# ✅ Auth
@app.post(
    "/register",
    tags=["Authentication"],
    summary="Жаңа қолданушыны тіркеу",
    description="Жаңа қолданушыны тіркеп, дерекқорға сақтайды. Тіркелу үшін тек username және password жеткілікті.",
    response_model=schemas.UserOut,
    responses={
        201: {
            "description": "Қолданушы сәтті тіркелді",
            "content": {
                "application/json": {
                    "example": {
                        "id": 7,
                        "username": "bek07"
                    }
                }
            }
        },
        400: {"description": "Қате сұраныс немесе қолданушы бұрыннан бар"},
    }
)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    hashed_password = get_password_hash(user.password)
    new_user = User(username=user.username, hashed_password=hashed_password, role="user")
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    logging.info("New user registered", extra={"username": user.username})
    return new_user



@app.post(
    "/login",
    tags=["Authentication"],
    summary="Қолданушыны жүйеге кіргізу",
    description="Қолданушы аты мен құпиясөз тексеріліп, егер дұрыс болса, JWT токен қайтарылады.",
    responses={
        200: {
            "description": "Сәтті авторизация",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "string.jwt.token",
                        "token_type": "bearer"
                    }
                }
            }
        },
        401: {"description": "Қолданушы аты немесе құпиясөз қате"},
        500: {"description": "Сервер қатесі"}
    }
)
async def login(user: UserLogin, db: AsyncSession = Depends(get_db)):
    db_user = await get_user_by_username(db, user.username)
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        logging.warning("Login failed", extra={"username": user.username})
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token(data={"sub": user.username})
    logging.info("User logged in", extra={"username": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


# ✅ User Info
from fastapi import APIRouter
router = APIRouter()

@router.get(
    "/users/me",
    tags=["Users"],
    summary="Ағымдағы қолданушы туралы мәлімет",
    description="JWT токен арқылы аутентификацияланған қолданушы туралы ақпаратты қайтарады.",
    response_model=schemas.UserOut,
    responses={
        200: {"description": "Қолданушы мәліметі сәтті қайтарылды"},
        401: {"description": "Авторизация қажет"},
    }
)
async def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user


from fastapi import status
from typing import List

@app.get(
    "/admin/users",
    tags=["Admin"],
    summary="Барлық қолданушыларды көру (тек админдерге)",
    description="Бұл эндпоинт тек 'admin' рөлі бар қолданушыларға ғана рұқсат етілген. Барлық тіркелген қолданушылар тізімін қайтарады.",
    response_model=List[schemas.UserOut],
    responses={
        200: {
            "description": "Қолданушылар сәтті алынды",
        },
        403: {
            "description": "Рұқсат жоқ (тек админдерге)",
            "content": {
                "application/json": {
                    "example": {"detail": "Not enough permissions"}
                }
            },
        },
    }
)
async def get_all_users(
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(require_role("admin"))
):
    result = await db.execute(select(models.User))
    users = result.scalars().all()
    return users
