from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
import models, schemas
from utils import get_current_user
from typing import List
from dependencies.redis import get_redis
import json
from models import Note, User
from schemas import NoteOut
from redis.asyncio.client import Redis  # ✅ дұрыс импорт
from celery_app import send_mock_email

router = APIRouter(prefix="/notes", tags=["Notes"])

# POST /notes
@router.post(
    "/",
    response_model=schemas.NoteOut,
    summary="Жаңа ескертпе қосу",
    description="Аутентификацияланған қолданушы үшін жаңа ескертпе жасайды.",
    responses={
        201: {
            "description": "Ескертпе сәтті жасалды",
            "content": {
                "application/json": {
                    "example": {"id": 1, "text": "Сабаққа дайындалу", "created_at": "2024-05-01T12:00:00Z"}
                }
            }
        },
        401: {"description": "Авторизация қажет"},
        422: {"description": "Валидация қатесі"}
    },
)
async def create_note(
    note: schemas.NoteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    redis: Redis = Depends(get_redis)  # ✅ міндетті аргумент
):
    new_note = Note(**note.dict(), owner_id=current_user.id)
    db.add(new_note)
    await db.commit()
    await db.refresh(new_note)

    # ✅ Кэшті тазарту
    pattern = f"notes:{current_user.id}:*"
    keys = await redis.keys(pattern)
    if keys:
        await redis.delete(*keys)
    return new_note

# GET /notes
@router.get(
    "/",
    response_model=list[schemas.NoteOut],
    summary="Барлық ескертпелерді алу",
    description="Аутентификацияланған қолданушының барлық ескертпелерін қайтарады (кэш қолданылады).",
    responses={
        200: {
            "description": "Ескертпелер тізімі сәтті қайтарылды",
            "content": {
                "application/json": {
                    "example": [
                        {"id": 1, "text": "Сабаққа дайындалу", "created_at": "2024-05-01T12:00:00Z"},
                        {"id": 2, "text": "Жаттығу жасау", "created_at": "2024-05-02T09:00:00Z"}
                    ]
                }
            }
        },
        401: {"description": "Авторизация қажет"}
    },
)
async def get_notes(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    redis: Redis = Depends(get_redis),
):
    cache_key = f"notes:{current_user.id}:list"
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)

    result = await db.execute(
        select(Note).where(Note.owner_id == current_user.id).limit(10)
    )
    notes = result.scalars().all()
    serialized = [schemas.NoteOut.from_orm(note).model_dump() for note in notes]

    # ✅ Fix: datetime сериализациясын қолдау
    await redis.set(cache_key, json.dumps(serialized, default=str), ex=300)

    return serialized

# GET /notes/{note_id}
@router.get(
    "/{note_id}",
    response_model=schemas.NoteOut,
    summary="Ескертпені алу (ID арқылы)",
    description="ID арқылы нақты ескертпені қайтарады. Тек иесі ғана көре алады.",
    responses={
        200: {
            "description": "Ескертпе сәтті қайтарылды",
            "content": {
                "application/json": {
                    "example": {"id": 1, "text": "Сабаққа дайындалу", "created_at": "2024-05-01T12:00:00Z"}
                }
            }
        },
        401: {"description": "Авторизация қажет"},
        404: {"description": "Ескертпе табылмады"}
    },
)
async def get_note(
    note_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Note).where(Note.id == note_id))
    note = result.scalar_one_or_none()
    if not note or note.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Note not found")
    return note

# PUT /notes/{note_id}
@router.put(
    "/{note_id}",
    response_model=schemas.NoteOut,
    summary="Ескертпені жаңарту",
    description="ID арқылы ескертпені жаңартады. Тек иесі ғана өзгерте алады.",
    responses={
        200: {
            "description": "Ескертпе сәтті жаңартылды",
            "content": {
                "application/json": {
                    "example": {"id": 1, "text": "Жаңартылған мәтін", "created_at": "2024-05-01T12:00:00Z"}
                }
            }
        },
        401: {"description": "Авторизация қажет"},
        404: {"description": "Ескертпе табылмады"},
        422: {"description": "Валидация қатесі"}
    },
)
async def update_note(
    note_id: int,
    updated_note: schemas.NoteUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    redis: Redis = Depends(get_redis)
):
    result = await db.execute(select(Note).where(Note.id == note_id))
    note = result.scalar_one_or_none()
    if not note or note.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Note not found")

    for key, value in updated_note.dict(exclude_unset=True).items():
        setattr(note, key, value)

    await db.commit()
    await db.refresh(note)

    # ✅ Кэшті тазарту
    pattern = f"notes:{current_user.id}:*"
    keys = await redis.keys(pattern)
    if keys:
        await redis.delete(*keys)

    return note

# DELETE /notes/{note_id}
@router.delete(
    "/{note_id}",
    summary="Ескертпені жою",
    description="ID арқылы ескертпені жояды. Тек иесі ғана өшіре алады.",
    responses={
        200: {
            "description": "Ескертпе сәтті жойылды",
            "content": {
                "application/json": {
                    "example": {"detail": "Note deleted successfully"}
                }
            }
        },
        401: {"description": "Авторизация қажет"},
        404: {"description": "Ескертпе табылмады"}
    },
)
async def delete_note(
    note_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    redis: Redis = Depends(get_redis)
):
    result = await db.execute(select(Note).where(Note.id == note_id))
    note = result.scalar_one_or_none()
    if not note or note.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Note not found")

    await db.delete(note)
    await db.commit()

    # ✅ Кэшті тазарту
    pattern = f"notes:{current_user.id}:*"
    keys = await redis.keys(pattern)
    if keys:
        await redis.delete(*keys)

    return {"detail": "Note deleted successfully"}

