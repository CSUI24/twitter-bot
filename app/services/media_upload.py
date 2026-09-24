from urllib.parse import urlsplit

import requests

from app.core.config import Settings
from app.core.exceptions import TwitterConfigurationError, TwitterServiceError
from app.services.twitter_client import TwitterClientProvider

MAX_IMAGE_BYTES = 1_048_576
MEDIA_UPLOAD_URL = "https://upload.x.com/i/media/upload.json"
ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}


class TwitterMediaUploader:
    def __init__(
        self,
        settings: Settings,
        client_provider: TwitterClientProvider,
    ) -> None:
        self.settings = settings
        self.client_provider = client_provider

    def upload_images(
        self,
        image_urls: list[str],
        existing_media_count: int = 0,
    ) -> list[str]:
        if not image_urls:
            return []
        if not self.settings.twitter_media_allowed_hosts:
            raise TwitterConfigurationError(
                "Set TWITTER_MEDIA_ALLOWED_HOSTS to the public R2 image host before attaching images."
            )

        for image_url in image_urls:
            self._validate_url(image_url)

        downloaded_images = []
        with requests.Session() as session:
            for image_url in image_urls:
                downloaded_images.append(self._download_image(session, image_url))

            has_gif = any(
                media_type == "image/gif" for _, media_type in downloaded_images
            )
            if has_gif and (len(downloaded_images) + existing_media_count > 1):
                raise TwitterServiceError(
                    "An animated GIF must be the only image attached to a tweet."
                )

            headers = self.client_provider.get_media_upload_headers()
            media_ids = []
            for image_bytes, media_type in downloaded_images:
                media_ids.append(
                    self._upload_image(session, headers, image_bytes, media_type)
                )
        return media_ids

    def _validate_url(self, image_url: str) -> None:
        parsed = urlsplit(image_url)
        host = (parsed.hostname or "").lower().rstrip(".")
        try:
            port = parsed.port
        except ValueError as exc:
            raise TwitterServiceError("Image URL has an invalid port.") from exc
        if (
            parsed.scheme != "https"
            or not host
            or parsed.username is not None
            or parsed.password is not None
            or port not in (None, 443)
            or host not in self.settings.twitter_media_allowed_hosts
        ):
            raise TwitterServiceError(
                "Image URL must use HTTPS and match TWITTER_MEDIA_ALLOWED_HOSTS."
            )

    def _download_image(
        self,
        session: requests.Session,
        image_url: str,
    ) -> tuple[bytes, str]:
        try:
            response = session.get(
                image_url,
                headers={"Accept": "image/jpeg,image/png,image/webp,image/gif"},
                timeout=(5, 20),
                allow_redirects=False,
                stream=True,
            )
            with response:
                if response.status_code != 200:
                    raise TwitterServiceError(
                        f"Could not download an attached image (HTTP {response.status_code})."
                    )

                content_length = response.headers.get("content-length")
                if content_length:
                    try:
                        if int(content_length) > MAX_IMAGE_BYTES:
                            raise TwitterServiceError(
                                "Each attached image must be no larger than 1 MB."
                            )
                    except ValueError:
                        pass

                image_bytes = bytearray()
                for chunk in response.iter_content(chunk_size=64 * 1024):
                    image_bytes.extend(chunk)
                    if len(image_bytes) > MAX_IMAGE_BYTES:
                        raise TwitterServiceError(
                            "Each attached image must be no larger than 1 MB."
                        )
        except requests.RequestException as exc:
            raise TwitterServiceError("Could not download an attached image.") from exc

        media_type = self._detect_image_type(bytes(image_bytes))
        if media_type is None:
            raise TwitterServiceError(
                "Attached images must be valid JPEG, PNG, WebP, or GIF files."
            )
        return bytes(image_bytes), media_type

    @staticmethod
    def _detect_image_type(image_bytes: bytes) -> str | None:
        if image_bytes.startswith(b"\xff\xd8\xff"):
            return "image/jpeg"
        if image_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
            return "image/png"
        if image_bytes.startswith((b"GIF87a", b"GIF89a")):
            return "image/gif"
        if (
            len(image_bytes) >= 12
            and image_bytes[:4] == b"RIFF"
            and image_bytes[8:12] == b"WEBP"
        ):
            return "image/webp"
        return None

    def _upload_image(
        self,
        session: requests.Session,
        headers: dict[str, str],
        image_bytes: bytes,
        media_type: str,
    ) -> str:
        try:
            initialize = session.post(
                MEDIA_UPLOAD_URL,
                params={
                    "command": "INIT",
                    "total_bytes": str(len(image_bytes)),
                    "media_type": media_type,
                    "media_category": "tweet_image",
                },
                headers=headers,
                timeout=(5, 30),
                allow_redirects=False,
            )
            if initialize.status_code not in (200, 202):
                raise TwitterServiceError(
                    self._x_upload_error(
                        "initialization", initialize.status_code, initialize.text,
                        initialize.headers.get("x-transaction-id")
                        or initialize.headers.get("x-request-id"),
                    )
                )
            media_id = initialize.json().get("media_id_string")
            if not isinstance(media_id, str) or not media_id:
                raise TwitterServiceError("X did not return a media ID.")

            append = session.post(
                MEDIA_UPLOAD_URL,
                params={
                    "command": "APPEND",
                    "media_id": media_id,
                    "segment_index": "0",
                },
                files={
                    "media": (
                        "image" + ALLOWED_IMAGE_TYPES[media_type],
                        image_bytes,
                        media_type,
                    )
                },
                headers=headers,
                timeout=(5, 30),
                allow_redirects=False,
            )
            if append.status_code not in (200, 204):
                raise TwitterServiceError(
                    self._x_upload_error(
                        "segment upload", append.status_code, append.text,
                        append.headers.get("x-transaction-id")
                        or append.headers.get("x-request-id"),
                    )
                )

            finalize = session.post(
                MEDIA_UPLOAD_URL,
                params={"command": "FINALIZE", "media_id": media_id},
                headers=headers,
                timeout=(5, 30),
                allow_redirects=False,
            )
            if finalize.status_code not in (200, 201):
                raise TwitterServiceError(
                    self._x_upload_error(
                        "finalization", finalize.status_code, finalize.text,
                        finalize.headers.get("x-transaction-id")
                        or finalize.headers.get("x-request-id"),
                    )
                )
            return media_id
        except requests.RequestException as exc:
            raise TwitterServiceError("Could not upload an image to X.") from exc
        except (ValueError, TypeError) as exc:
            raise TwitterServiceError("X returned an invalid image upload response.") from exc

    @staticmethod
    def _x_upload_error(
        stage: str,
        status_code: int,
        response_body: str,
        request_id: str | None,
    ) -> str:
        detail = " ".join(response_body.split())[:300]
        message = f"X rejected image upload {stage} (HTTP {status_code})"
        if detail:
            message += f": {detail}"
        if request_id:
            message += f" [request ID: {request_id}]"
        return message + "."
