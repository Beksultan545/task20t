from fastapi import APIRouter, Depends
from utils import get_current_user
from celery_app import send_mock_email

router = APIRouter()

@router.post("/trigger-task")
async def trigger_task(current_user=Depends(get_current_user)):
    send_mock_email.delay(current_user.username + "@example.com")
    return {"message": "Task started"}
