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
        cookies = self._load_cookies()

        client = TwitterOpenapiPython()
        platform_header = f'"{self.settings.twitter_platform_header}"'
        client.additional_api_headers = {"sec-ch-ua-platform": platform_header}
        client.additional_browser_headers = {"sec-ch-ua-platform": platform_header}
        return client.get_client_from_cookies(cookies=cookies)

    def _load_cookies(self) -> dict[str, str]:
        if not self.settings.twitter_auth_token or not self.settings.twitter_ct0:
            raise TwitterConfigurationError(
                "Set TWITTER_AUTH_TOKEN and TWITTER_CT0 in .env for authenticated tweet actions."
            )

        return {
            "auth_token": self.settings.twitter_auth_token,
            "ct0": self.settings.twitter_ct0,
        }
