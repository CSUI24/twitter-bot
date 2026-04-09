class TwitterConfigurationError(Exception):
    """Raised when the Twitter client cannot be configured."""


class TwitterServiceError(Exception):
    """Raised when the Twitter API operation fails."""

    def __init__(self, message: str, status_code: int = 502) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
