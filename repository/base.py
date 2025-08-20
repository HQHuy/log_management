from motor.motor_asyncio import AsyncIOMotorClient
from core.config import settings
from typing import Optional

class DatabaseRepository:
    def __init__(self, mongo: AsyncIOMotorClient) -> None:
        self._mongo = mongo
        self.database = self._mongo[settings.DATABASE_NAME]

    def get_collection(self, name: Optional[str] = None):
        collection_name = name or settings.COLLECTION_NAME
        return self.database[collection_name]
