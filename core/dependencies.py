from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import Depends, Request
from loguru import logger

from repository.log import LogRepository

def get_mongo_client(request: Request):
    logger.info(request.app.state.mongo_client)
    return request.app.state.mongo_client


def get_log_repo(mongo: AsyncIOMotorClient = Depends(get_mongo_client)):
    return LogRepository(mongo)
