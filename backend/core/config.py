from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "Whats-Good"
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    REDIS_URL: str = os.getenv("UPSTASH_REDIS_URL")
    REDIS_HOST: str = os.getenv("UPSTASH_REDIS_HOST")
    REDIS_PORT: int = os.getenv("UPSTASH_REDIS_PORT")
    REDIS_PASSWORD: str = os.getenv("UPSTASH_REDIS_PASSWORD")
    SECRET_KEY: str = os.getenv('SECRET_KEY')
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30


    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()