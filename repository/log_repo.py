from motor.motor_asyncio import AsyncIOMotorClient
from repository.base import DatabaseRepository
from core.config import settings


class LogRepository(DatabaseRepository):
    def __init__(self, mongo: AsyncIOMotorClient) -> None:
        super().__init__(mongo)
        self.coll = self.get_collection()

    async def get_date(self):
        pipeline = [
            {
                '$group': {
                    '_id': {
                        '$dateToString': {
                            'format': '%Y-%m-%d',
                            'date': '$timestamp',
                        }
                    }
                }
            },
            { '$sort': { '_id': -1 } },
            { '$project': { 'date': '$_id', '_id': 0 } }
        ]

        date_lst = self.coll.aggregate(pipeline)

        return [ doc['date'] async for doc in date_lst ]
    
    