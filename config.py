from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="allow")  # Немесе extra="ignore" болса да болады

    # PostgreSQL
    database_url: str

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379

    # FastAPI
    secret_key: str

    # Celery
    celery_broker_url: str
    celery_result_backend: str

settings = Settings()
