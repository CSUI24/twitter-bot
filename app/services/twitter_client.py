import json
from pathlib import Path
from threading import Lock

from twitter_openapi_python import TwitterOpenapiPython
from twitter_openapi_python.client import TwitterOpenapiPythonClient

from app.core.config import Settings
from app.core.exceptions import TwitterConfigurationError


class TwitterClientProvider:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._client: TwitterOpenapiPythonClient | None = None
        self._lock = Lock()

    def get_client(self) -> TwitterOpenapiPythonClient:
        if self._client is None:
            with self._lock:
                if self._client is None:
                    self._client = self._build_client()

        return self._client

    def _build_client(self) -> TwitterOpenapiPythonClient:
        cookies = self._load_cookies(self.settings.cookie_file)

        if "auth_token" not in cookies or "ct0" not in cookies:
            raise TwitterConfigurationError(
                "cookie.json must include at least 'auth_token' and 'ct0' for authenticated tweet actions."
            )

        client = TwitterOpenapiPython()
        platform_header = f'"{self.settings.twitter_platform_header}"'
        client.additional_api_headers = {"sec-ch-ua-platform": platform_header}
        client.additional_browser_headers = {"sec-ch-ua-platform": platform_header}
        return client.get_client_from_cookies(cookies=cookies)

    @staticmethod
    def _load_cookies(cookie_file: Path) -> dict[str, str]:
        if not cookie_file.exists():
            raise TwitterConfigurationError(f"Cookie file not found: {cookie_file}")

        try:
            with cookie_file.open("r", encoding="utf-8") as file:
                payload = json.load(file)
        except json.JSONDecodeError as exc:
            raise TwitterConfigurationError(f"Invalid JSON in cookie file: {cookie_file}") from exc

        if isinstance(payload, list):
            cookies = {
                item["name"]: item["value"]
                for item in payload
                if isinstance(item, dict) and "name" in item and "value" in item
            }
        elif isinstance(payload, dict):
            cookies = {str(key): str(value) for key, value in payload.items()}
        else:
            raise TwitterConfigurationError("Cookie file must contain a JSON object or a list of cookie objects.")

        if not cookies:
            raise TwitterConfigurationError("Cookie file does not contain any usable cookies.")

        return cookies
