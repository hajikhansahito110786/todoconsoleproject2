from datetime import datetime
from sqlmodel import SQLModel, Field
from typing import Optional
import uuid


class UserBase(SQLModel):
    username: str = Field(min_length=1, max_length=100, unique=True)
    email: str = Field(regex=r'^[\w\.-]+@[\w\.-]+\.\w+$', unique=True)


class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str = Field(min_length=1)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class UserCreate(UserBase):
    password: str = Field(min_length=1)


class UserUpdate(SQLModel):
    username: Optional[str] = Field(default=None, min_length=1, max_length=100)
    email: Optional[str] = Field(default=None, regex=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    password: Optional[str] = Field(default=None, min_length=1)


class UserRead(UserBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime