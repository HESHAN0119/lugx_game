# lugx_backend/app/main.py

from operator import or_
from fastapi import FastAPI, Depends,HTTPException, status,Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from passlib.context import CryptContext
from models import Game,GameRead,GameUpdate,User,Order
from deps import get_db,UserCreate,GameCreate,LoginRequest,OrderCreate,OrderRead
from pw_hashing import hash_password,verify_password
from access_token import create_access_token
from clickhouse_driver import Client
import json
from get_current_user import get_current_user
import logging
import time
from clickhouse_driver.errors import NetworkError
from datetime import datetime
from fastapi import HTTPException, Request

#test6
logging.basicConfig(level=logging.INFO)
logger=logging.getLogger(__name__)

app = FastAPI()
# app.include_router(user_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic model for request/response


# @app.get("/api/games")
# async def get_games(db: AsyncSession = Depends(get_db)):
#     result = await db.execute(select(Game))
#     games = result.scalars().all()
#     return [
#         {"id": game.id, "name": game.name, "price": game.price}
#         for game in games
#     ]

# Pydantic schema for response


# from pydantic import BaseModel

@app.get("/api/games", response_model=List[GameRead])
async def read_games(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Game))
    games = result.scalars().all()
    return games

@app.post("/api/games")
async def create_game(game: GameCreate, db: AsyncSession = Depends(get_db)):
    new_game = Game(name=game.name, price=game.price, updated_time = datetime.now())
    db.add(new_game)
    await db.commit()
    await db.refresh(new_game)
    return {
        "id": new_game.id,
        "name": new_game.name,
        "price": new_game.price
    }

@app.post("/api/users")
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    # Check if username already exists
    result = await db.execute(select(User).where(User.username == user.username))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists.")

    hashed_pw = hash_password(user.password)

    new_user = User(
        username=user.username,
        email=user.email,
        password=hashed_pw
        updated_time = datetime.now()
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return {
        "id": new_user.id,
        "username": new_user.username,
        "email": new_user.email,
    }


@app.put("/api/games/{game_id}", response_model=GameRead)
async def update_game(
    game_id: int,
    game_update: GameUpdate,
    db: AsyncSession = Depends(get_db)
):
    # Fetch the existing game
    result = await db.execute(select(Game).where(Game.id == game_id))
    game = result.scalar_one_or_none()

    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")

    # Update only the fields provided
    if game_update.name is not None:
        game.name = game_update.name

    if game_update.price is not None:
        game.price = game_update.price

    db.add(game)
    await db.commit()
    await db.refresh(game)

    return game



@app.post("/api/users/login")
async def login_user(user: LoginRequest, db: AsyncSession = Depends(get_db)):
    # your lookup logic...
    result = await db.execute(
        select(User).where(
            (User.username == user.username_or_email) | (User.email == user.username_or_email)
        )
    )
    db_user = result.scalar_one_or_none()

    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    if not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    access_token = create_access_token(
        data={"sub": str(db_user.id), "username": db_user.username}
    )

    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/orders", response_model=OrderRead)
async def place_order(
    order_data: OrderCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Fetch the game
    result = await db.execute(
        select(Game).where(Game.id == order_data.game_id)
    )
    game = result.scalar_one_or_none()

    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    total_price = game.price * order_data.quantity

    new_order = Order(
        user_id=current_user.id,
        game_id=game.id,
        quantity=order_data.quantity,
        total_price=total_price,
        updated_time = datetime.now()
    )

    db.add(new_order)
    await db.commit()
    await db.refresh(new_order)

    return new_order

# Initialize ClickHouse client with retry
def init_clickhouse_client():
    max_retries = 5
    retry_delay = 2
    for attempt in range(max_retries):
        try:
            client = Client(host='clickhouse', port=9000, user='default', database='lugx_clickhouse_db')
            client.execute('SELECT 1')  # Test connection
            logger.info("Connected to ClickHouse")
            return client
        except NetworkError as e:
            logger.warning(f"ClickHouse connection attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                logger.error("Failed to connect to ClickHouse after retries")
                raise

clickhouse_client = init_clickhouse_client()




logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.post("/api/analytics")
async def receive_analytics(request: Request):
    logger.info("Received request to /api/analytics")
    try:
        data = await request.json()
        logger.info(f"Request payload: {data}")
    except json.JSONDecodeError:
        logger.error("Invalid JSON payload received")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    required_fields = ["event_type", "url", "total_time_ms", "total_clicks", "clicked_items", "max_scroll_percent", "timestamp"]
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        logger.error(f"Missing fields: {missing_fields}")
        raise HTTPException(status_code=400, detail=f"Missing fields: {missing_fields}")

    try:
        event_type = data["event_type"]
        url = data["url"]
        total_time_ms = int(data["total_time_ms"])
        total_clicks = int(data["total_clicks"])
        clicked_items_raw = data["clicked_items"]
        max_scroll_percent = int(data["max_scroll_percent"])
        timestamp_str = data["timestamp"]
        timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
    except (ValueError, TypeError) as e:
        logger.error(f"Invalid data format: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid data format: {str(e)}")

    try:
        clicked_items = [(item.get("tag", ""), item.get("text", "")) for item in clicked_items_raw]
    except (TypeError, AttributeError):
        logger.error("Invalid clicked_items format")
        raise HTTPException(status_code=400, detail="Invalid clicked_items format")

    print("*********************", event_type)
    print("*********************", max_scroll_percent)
    print("*********************", timestamp_str)
    print("*********************", clicked_items)
    logger.info(f"Processed data: event_type={event_type}, url={url}, total_time_ms={total_time_ms}, total_clicks={total_clicks}, clicked_items={clicked_items}, max_scroll_percent={max_scroll_percent}, timestamp={timestamp}")

    try:
        clickhouse_client.execute(
            """
            INSERT INTO lugx_clickhouse_db.page_summary
            (event_type, url, total_time_ms, total_clicks, clicked_items, max_scroll_percent, timestamp)
            VALUES
            """,
            [(event_type, url, total_time_ms, total_clicks, clicked_items, max_scroll_percent, timestamp)],
            types_check=False
        )
        logger.info("Data inserted into ClickHouse")
    except Exception as e:
        logger.error(f"ClickHouse insert failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to store analytics data")

    return {"status": "ok"}




@app.post("/api/analytics/shop")
async def receive_analytics2(request: Request):
    logger.info("Received request to /api/analytics")
    try:
        data = await request.json()
        logger.info(f"Request payload: {data}")
    except json.JSONDecodeError:
        logger.error("Invalid JSON payload received")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    required_fields = ["event_type", "url", "total_time_ms", "total_clicks", "clicked_items", "max_scroll_percent", "timestamp"]
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        logger.error(f"Missing fields: {missing_fields}")
        raise HTTPException(status_code=400, detail=f"Missing fields: {missing_fields}")

    try:
        event_type = data["event_type"]
        url = data["url"]
        total_time_ms = int(data["total_time_ms"])
        total_clicks = int(data["total_clicks"])
        clicked_items_raw = data["clicked_items"]
        max_scroll_percent = int(data["max_scroll_percent"])
        timestamp_str = data["timestamp"]
        timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
    except (ValueError, TypeError) as e:
        logger.error(f"Invalid data format: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid data format: {str(e)}")

    try:
        clicked_items = [(item.get("tag", ""), item.get("text", "")) for item in clicked_items_raw]
    except (TypeError, AttributeError):
        logger.error("Invalid clicked_items format")
        raise HTTPException(status_code=400, detail="Invalid clicked_items format")

    print("*********************", event_type)
    print("*********************", max_scroll_percent)
    print("*********************", timestamp_str)
    print("*********************", clicked_items)
    logger.info(f"Processed data: event_type={event_type}, url={url}, total_time_ms={total_time_ms}, total_clicks={total_clicks}, clicked_items={clicked_items}, max_scroll_percent={max_scroll_percent}, timestamp={timestamp}")

    try:
        clickhouse_client.execute(
            """
            INSERT INTO lugx_clickhouse_db.page_summary
            (event_type, url, total_time_ms, total_clicks, clicked_items, max_scroll_percent, timestamp)
            VALUES
            """,
            [(event_type, url, total_time_ms, total_clicks, clicked_items, max_scroll_percent, timestamp)],
            types_check=False
        )
        logger.info("Data inserted into ClickHouse")
    except Exception as e:
        logger.error(f"ClickHouse insert failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to store analytics data")

    return {"status": "ok"}



@app.post("/api/analytics/product_details")
async def receive_analytics2(request: Request):
    logger.info("Received request to /api/analytics")
    try:
        data = await request.json()
        logger.info(f"Request payload: {data}")
    except json.JSONDecodeError:
        logger.error("Invalid JSON payload received")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    required_fields = ["event_type", "url", "total_time_ms", "total_clicks", "clicked_items", "max_scroll_percent", "timestamp"]
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        logger.error(f"Missing fields: {missing_fields}")
        raise HTTPException(status_code=400, detail=f"Missing fields: {missing_fields}")

    try:
        event_type = data["event_type"]
        url = data["url"]
        total_time_ms = int(data["total_time_ms"])
        total_clicks = int(data["total_clicks"])
        clicked_items_raw = data["clicked_items"]
        max_scroll_percent = int(data["max_scroll_percent"])
        timestamp_str = data["timestamp"]
        timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
    except (ValueError, TypeError) as e:
        logger.error(f"Invalid data format: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid data format: {str(e)}")

    try:
        clicked_items = [(item.get("tag", ""), item.get("text", "")) for item in clicked_items_raw]
    except (TypeError, AttributeError):
        logger.error("Invalid clicked_items format")
        raise HTTPException(status_code=400, detail="Invalid clicked_items format")

    print("*********************", event_type)
    print("*********************", max_scroll_percent)
    print("*********************", timestamp_str)
    print("*********************", clicked_items)
    logger.info(f"Processed data: event_type={event_type}, url={url}, total_time_ms={total_time_ms}, total_clicks={total_clicks}, clicked_items={clicked_items}, max_scroll_percent={max_scroll_percent}, timestamp={timestamp}")

    try:
        clickhouse_client.execute(
            """
            INSERT INTO lugx_clickhouse_db.page_summary
            (event_type, url, total_time_ms, total_clicks, clicked_items, max_scroll_percent, timestamp)
            VALUES
            """,
            [(event_type, url, total_time_ms, total_clicks, clicked_items, max_scroll_percent, timestamp)],
            types_check=False
        )
        logger.info("Data inserted into ClickHouse")
    except Exception as e:
        logger.error(f"ClickHouse insert failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to store analytics data")

    return {"status": "ok"}


# @app.post("/api/analytics")
# async def receive_analytics(request: Request):
#     data = await request.json()
#     # current_user: User = Depends(get_current_user)
# #     data={
# #     "event_type": "click",
# #     "url": "/home",
# #     "element": "button",
# #     "text": "Buy Now",
# #     "scroll_percent": "50.5",
# #     "duration_ms": "123.7",
# #     "timestamp": datetime.fromisoformat("2025-06-30T22:51:58")
# # }
    
    
#     # # Extract fields safely
#     # event_type = data.get("event_type")
#     # url = data.get("url")
#     # element = data.get("element")
#     # text = data.get("text")

#     event_type = data.get("event_type", "page_summary")
#     url = data.get("url")
#     total_time_ms = int(data.get("total_time_ms", 0))
#     total_clicks = int(data.get("total_clicks", 0))
#     clicked_items_raw = data.get("clicked_items", [])
#     max_scroll_percent = int(data.get("max_scroll_percent", 0))
#     # timestamp_str = data.get("timestamp")

#     timestamp_str = data.get("timestamp")
#     timestamp = datetime.fromisoformat(
#         timestamp_str.replace("Z", "+00:00")
#     )

#     clicked_items = [
#         (item.get("tag", ""), item.get("text", ""))
#         for item in clicked_items_raw
#     ]


#     print("*********************",event_type)
#     print("*********************",max_scroll_percent)

#     print("*********************",timestamp_str)
#     print("*********************",clicked_items)
#     # # scroll_percent → must be float
#     # scroll_percent = data.get("scroll_percent")
#     # # if scroll_percent is None:
#     # #     scroll_percent = 0.0
#     # # else:
#     # #     scroll_percent = float(scroll_percent)

#     # # duration_ms → must be UInt32 → non-negative integer
#     # duration_ms = data.get("duration_ms")
#     # # if duration_ms is None:
#     # #     duration_ms = 0
#     # # else:
#     # #     # handle if duration_ms arrives as string, float etc.
#     # #     duration_ms = int(float(duration_ms))
#     # #     duration_ms = max(0, duration_ms)   # avoid negative values

#     # # timestamp → must be datetime
#     # timestamp = data.get("timestamp")
#     # # if timestamp_str:
#     # #     timestamp = datetime.fromisoformat(timestamp_str)
#     # # else:
#     # #     timestamp = datetime.now()

#     # # Prepare ClickHouse insert
#     clickhouse_client.execute(
#             """
#             INSERT INTO lugx_clickhouse_db.page_summary
#             (event_type, url, total_time_ms, total_clicks, clicked_items, max_scroll_percent, timestamp)
#             VALUES
#             """,
#             [
#                 (
#                     event_type,
#                     url,
#                     total_time_ms,
#                     total_clicks,
#                     clicked_items,
#                     max_scroll_percent,
#                     timestamp
#                 )
#             ],
#             types_check=False
#         )

#     return {"status": "ok"}









# @app.post("/api/users/login")
# async def login_user(
#     user: LoginRequest, 
#     db: AsyncSession = Depends(get_db)
# ):
#     result = await db.execute(
#         select(User).where(
#             or_(
#                 User.username == user.username_or_email,
#                 User.email == user.username_or_email
#             )
#         )
#     )
#     db_user = result.scalar_one_or_none()

#     if not db_user:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Invalid username/email or password"
#         )
    
#     if not verify_password(user.password, db_user.password):
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Invalid username/email or password"
#         )

#     return {
#         "message": f"User '{db_user.username}' logged in successfully."
#     }
