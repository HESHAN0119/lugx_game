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
