from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from loguru import logger


from core.config import settings
from api.routes import router as api_router
from db.database import create_start_app_handler, create_stop_app_handler


def get_application():
    application = FastAPI(
        title=settings.PROJECT_NAME,
        docs_url='/docs',
    )

    application.add_event_handler('startup', create_start_app_handler(application))
    application.add_event_handler('shutdown', create_stop_app_handler(application))

    application.include_router(api_router)


    application.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origins) for origins in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    logger.info('App Startup Success')

    return application

app = get_application()

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)