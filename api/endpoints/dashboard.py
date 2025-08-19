from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
import json
from loguru import logger

from core.dependencies import ( get_log_repo )
from repository.log_repo import LogRepository

router = APIRouter()


@router.get('/data_collection/date')
async def collect_date(log_repo: LogRepository = Depends(get_log_repo)):
    
    result = await log_repo.get_date()
    return result

