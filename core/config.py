import os
from dotenv import load_dotenv
from typing import ClassVar
from pydantic_settings import BaseSettings

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: ClassVar[str] = os.getenv('PROJECT_NAME', 'App')
    API_PREFIX: ClassVar[str] = ''
    BACKEND_CORS_ORIGINS = ['*']
    DATABASE_URL = os.getenv('MONGODB_URL', '')
    LOGGING_CONFIG_FILE = os.path.join(BASE_DIR, 'logging.ini')

settings = Settings()