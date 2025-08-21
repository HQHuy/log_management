from typing import Any, List

from motor.motor_asyncio import AsyncIOMotorClient
from .base import DatabaseRepository


class LogRepository(DatabaseRepository):
    def __init__(self, mongo: AsyncIOMotorClient) -> None:
        super().__init__(mongo)
        self.coll = self.get_collection()

    async def get_date_from_db(self):
        pipeline = [
            {
                '$group': {
                    '_id': {
                        '$dateToString': {
                            'format': '%Y-%m-%d',
                            'date': '$timestamp',
                            'timezone': '+07:00'
                        }
                    }
                }
            },
            { '$sort': { '_id': -1 } },
        ]

        date_lst = self.coll.aggregate(pipeline=pipeline)
        return [ doc['_id'] async for doc in date_lst ]
    
    async def get_data(self, pipeline_custom):
        data = await self.coll.aggregate(pipeline=pipeline_custom).to_list()
        return data

    async def get_data_find(self, query):
        data = await self.coll.find(query).to_list()
        return data