from pydantic_settings import BaseSettings
from functools import lru_cache
from pydantic import (
    AnyUrl, 
    BeforeValidator,
    computed_field,
    field_validator
)
from typing import List



class Settings(BaseSettings):
    PROJECT_NAME: str
    debug: bool
    secret_key: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    SECRET_KEY: str
    ENCRYPTION_ALGORITHM: str
    MONGODB_URI: str
    SUPER_ADMIN_SEED_TOKEN: str | None = None
    API_STR: str = "api"
    API_VERSION: str
    PORT: int
    ALLOWED_ADMIN_EMAILS: str = ""
    SUPABASE_URL : str
    SUPABASE_KEY : str
    JWT_SECRET: str
    N8N_WEBHOOK_URL: str

    @computed_field
    @property
    def admin_emails_list(self) -> List[str]:
        """Parse comma-separated admin emails into a list"""
        if not self.ALLOWED_ADMIN_EMAILS:
            return []
        return [email.strip() for email in self.ALLOWED_ADMIN_EMAILS.split(',') if email.strip()]

    @computed_field
    @property
    def API_BASE_PATH(self) -> str:
        return f"/{self.API_STR}/{self.API_VERSION}"


    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()


