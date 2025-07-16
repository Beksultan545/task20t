from celery import Celery
import time

celery_app = Celery(
    "worker",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/0"
)

celery_app.conf.timezone = "Asia/Almaty"


@celery_app.task
def send_mock_email(email: str):
    time.sleep(10)
    print(f"✅ Email sent to {email}")