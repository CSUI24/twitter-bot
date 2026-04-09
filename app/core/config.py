import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    app_name: str
    app_host: str
    app_port: int
    app_reload: bool
    cookie_file: Path
    twitter_platform_header: str


@lru_cache
def get_settings() -> Settings:
    cookie_file = Path(os.getenv("TWITTER_COOKIE_FILE", "cookie.json")).expanduser()

    return Settings(
        app_name=os.getenv("APP_NAME", "Twitter Service"),
        app_host=os.getenv("API_HOST", "0.0.0.0"),
        app_port=int(os.getenv("API_PORT", "8000")),
        app_reload=os.getenv("API_RELOAD", "false").lower() == "true",
        cookie_file=cookie_file,
        twitter_platform_header=os.getenv("TWITTER_SEC_CH_UA_PLATFORM", "Windows"),
    )
