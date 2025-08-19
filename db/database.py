from motor.motor_asyncio import AsyncIOMotorClient
# from pymongo import MongoClient
from fastapi import FastAPI
from typing import Optional
from datetime import timezone
import logging

from ..main import app

from core.config import settings
logger = logging.getLogger(__name__)

class MongoDB():
    client: Optional[AsyncIOMotorClient] = None # type: ignore

mongodb = MongoDB()

def mongo_startup(app: FastAPI):
    if app is None:
        logger.error('app is None')
        raise

    logger.info('Connect to MongoDB')

    mongo_client = AsyncIOMotorClient(
        settings.DATABASE_URL,
        tz_aware=True,
        tzinfo=timezone.utc
    )

    mongodb.client = mongo_client
    app.state.mongo_client = mongo_client
    logger.info('Connect success')
    print('values', app.state.mongo_client)
    # app.state.mongo_client.close()
    # app.state.    
    # logger.info('Shutdown db')
    async def start_up():
        app.state.mongo_client.close()
        logger.info('shutdown db')
    return start_up
    
    

# mongo_startup(app)