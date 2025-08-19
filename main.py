from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn


from core.config import settings
from db.database import mongo_startup

def get_application():
    application = FastAPI(
        title=settings.PROJECT_NAME,
        docs_url='/docs',
    )

    application.add_event_handler('startup', mongo_startup(application))


    application.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origins) for origins in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return application

app = get_application()

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)