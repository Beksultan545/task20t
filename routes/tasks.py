from fastapi import APIRouter, Depends
from utils import get_current_user
from celery_app import send_mock_email

router = APIRouter(tags=["Tasks"])

@router.post(
    "/trigger-task",
    summary="Тапсырманы асинхронды түрде бастау",
    description="Аутентификацияланған қолданушы үшін Celery арқылы email-тапсырманы триггерлейді.",
    responses={
        200: {
            "description": "Тапсырма сәтті басталды",
            "content": {
                "application/json": {
                    "example": {"message": "Task started"}
                }
            }
        },
        401: {"description": "Авторизация қажет"}
    },
)
async def trigger_task(current_user=Depends(get_current_user)):
    send_mock_email.delay(current_user.username + "@example.com")
    return {"message": "Task started"}
