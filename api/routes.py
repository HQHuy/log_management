from fastapi import APIRouter
from fastapi.responses import JSONResponse
from datetime import datetime, tzinfo
from loguru import logger

from .endpoints import dashboard as dashboard_rou

router = APIRouter()

@router.get('/api/check')
def health_check():
    try:
        return JSONResponse(content={
            'status': 'OK',
            'timestamp': datetime.now().isoformat(" ", "minutes")
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(content={
            'status': 'ERROR',
            'error': str(e),
            'timestamp': datetime.now().isoformat(" ", "minutes")
            },
            status_code=503
        )
    
    
router.include_router(dashboard_rou.router, tags=['dashboard'], prefix='/dashboard')