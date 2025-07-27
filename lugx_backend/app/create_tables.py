# lugx_backend/app/create_tables.py

import asyncio
from database import engine, Base
from models import Game

async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

if __name__ == "__main__":
    asyncio.run(create_tables())
