import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    app_name: str
    app_host: str
    app_port: int
    app_reload: bool
    service_bearer_token: str | None
    twitter_auth_token: str | None
    twitter_ct0: str | None
    twitter_platform_header: str


@lru_cache
def get_settings() -> Settings:
    return Settings(
        app_name=os.getenv("APP_NAME", "Twitter Service"),
        app_host=os.getenv("API_HOST", "0.0.0.0"),
        app_port=int(os.getenv("API_PORT", "8000")),
        app_reload=os.getenv("API_RELOAD", "false").lower() == "true",
        service_bearer_token=os.getenv("SERVICE_BEARER_TOKEN"),
        twitter_auth_token=os.getenv("TWITTER_AUTH_TOKEN"),
        twitter_ct0=os.getenv("TWITTER_CT0"),
        twitter_platform_header=os.getenv("TWITTER_SEC_CH_UA_PLATFORM", "Windows"),
    )
