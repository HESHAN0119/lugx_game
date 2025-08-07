# lugx_backend/app/models.py

from sqlalchemy import Column, Integer, String, Float,ForeignKey
from database import Base
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import relationship

class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    price = Column(Float)
    orders = relationship("Order", back_populates="game")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    orders = relationship("Order", back_populates="user")

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    game_id = Column(Integer, ForeignKey("games.id"))
    quantity = Column(Integer, nullable=False)
    total_price = Column(Float, nullable=False)

    user = relationship("User", back_populates="orders")
    game = relationship("Game", back_populates="orders")

# class GameCreate(BaseModel):
#     name: str
#     price: float

# class UserCreate(BaseModel):
#     user_name: str
#     password: str


class GameRead(BaseModel):
    id: int
    name: str
    price: float

    class Config:
        orm_mode = True  # To convert from SQLAlchemy models


class GameUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None



# # app/api/routes_games.py
# from fastapi import APIRouter, Depends
# from sqlalchemy.ext.asyncio import AsyncSession
# from app.schemas.game import GameCreate
# from app.db.session import get_db
# from app.crud import game as crud_game

# router = APIRouter()


# @router.post("/")
# async def create_game(game: GameCreate, db: AsyncSession = Depends(get_db)):
#     return await crud_game.create_game(db, game)
