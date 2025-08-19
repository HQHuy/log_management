from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from contextlib import contextmanager
from fastapi import FastAPI
from typing import Optional
from datetime import timezone
from loguru import logger


from core.config import settings

class MongoDB():
    client: Optional[AsyncIOMotorClient] = None

mongodb = MongoDB()

def mongo_startup(app: FastAPI):
    if app is None:
        logger.error('App is None')
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
    # print('values', app.state.mongo_client)

def mongo_shutdown(app: FastAPI):
    logger.info('Closing the MongoDB connection...')
    mongo_client = getattr(app.state, "mongo_client", None)

    if mongo_client:
        mongo_client.close()
        logger.info('MongoDB connection closed!')
    else:
        logger.warning('Not found mongoDB')

def create_start_app_handler(app: FastAPI):
    def start_app():
        mongo_startup(app)
    return start_app

def create_stop_app_handler(app: FastAPI):
    def stop_app():
        mongo_shutdown(app)
    return stop_app

@contextmanager
def get_mongodb():
    try:
        with MongoClient() as client:
            db = client[settings.DATABASE_NAME]
            yield db
    except Exception as e:
        print('Error:', str(e))
        raise
# mongo_startup(app)