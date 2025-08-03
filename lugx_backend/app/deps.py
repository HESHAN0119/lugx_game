# lugx_backend/app/deps.py

from database import AsyncSessionLocal
from pydantic import BaseModel

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class GameCreate(BaseModel):
    name: str
    price: float
    release_date: str

# class UserCreate(BaseModel):
#     user_name: str
#     password: str

class LoginRequest(BaseModel):
    username_or_email: str
    password: str

class OrderCreate(BaseModel):
    game_id: int
    quantity: int

class OrderRead(BaseModel):
    id: int
    user_id: int
    game_id: int
    quantity: int
    total_price: float

    class Config:
        orm_mode = True