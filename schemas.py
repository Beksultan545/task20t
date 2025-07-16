# schemas.py
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime

class UserCreate(BaseModel):
    username: str = Field(..., description="Қолданушының логині", example="bek07")
    password: str = Field(..., description="Құпиясөз (ең аз дегенде 6 таңба)", example="Jans2007")

class UserLogin(BaseModel):
    username: str = Field(..., description="Қолданушы аты", example="bek07")
    password: str = Field(..., description="Құпиясөз", example="Jans2007")

class UserOut(BaseModel):
    id: int = Field(..., description="Қолданушының ID нөмірі", example=7)
    username: str = Field(..., description="Қолданушы аты", example="bek07")

    model_config = ConfigDict(from_attributes=True)


class UserRead(BaseModel):
    id: int
    username: str

    model_config = ConfigDict(from_attributes=True)  # Pydantic v2-де 'orm_mode' орнына

class NoteCreate(BaseModel):
    text: str = Field(..., description="Ескертпе мәтіні", example="Сабаққа дайындалу")

class NoteUpdate(BaseModel):
    text: str = Field(..., description="Жаңартылған ескертпе мәтіні", example="Жаттығу жасау")

class NoteOut(BaseModel):
    id: int = Field(..., description="Ескертпенің бірегей ID нөмірі", example=1)
    text: str = Field(..., description="Ескертпе мәтіні", example="Сабаққа дайындалу")
    created_at: datetime = Field(..., description="Ескертпе жасалған уақыт (UTC)", example="2024-05-01T12:00:00Z")

    model_config = ConfigDict(from_attributes=True)