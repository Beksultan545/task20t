from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    rate_limit: int = Field(default=100, alias="RATE_LIMIT")
    rate_limit_window: int = Field(default=60, alias="RATE_LIMIT_WINDOW")
    # қалғандарын қалдыра бер

    model_config = {
        "env_file": ".env",
        "extra": "allow"
    }

settings = Settings()
