import os
from dotenv import load_dotenv
from typing import ClassVar, List
from pydantic_settings import BaseSettings

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))
load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: ClassVar[str] = os.getenv('PROJECT_NAME', 'App')
    API_PREFIX: ClassVar[str] = ''
    BACKEND_CORS_ORIGINS: ClassVar[List] = ['*']
    DATABASE_URL: ClassVar[str] = os.getenv('MONGODB_URL', '')
    DATABASE_NAME: ClassVar[str] = os.getenv('DB_NAME', '')
    COLLECTION_NAME: ClassVar[str] = os.getenv('COLLECTION_NAME', '')
    LOGGING_CONFIG_FILE: ClassVar[str] = os.path.join(BASE_DIR, 'logging.ini')
    OUTPUT_BASE_DIR: ClassVar[str] = os.path.join(BASE_DIR, 'output')
    # UPLOAD_BASE_DIR: ClassVar[str] = os.path.join(BASE_DIR, 'upload')
    BACKUP_BASE_DIR: ClassVar[str] = os.path.join(BASE_DIR, 'backup')

settings = Settings()