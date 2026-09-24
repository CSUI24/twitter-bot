from typing import Any

from pydantic import BaseModel, Field, HttpUrl, model_validator


class CreateTweetRequest(BaseModel):
    tweet_text: str = Field(..., min_length=1, description="Tweet body.")
    media_ids: list[str] | None = Field(
        default=None,
        max_length=4,
        description="Optional media IDs.",
    )
    image_urls: list[HttpUrl] | None = Field(
        default=None,
        max_length=4,
        description="Public HTTPS image URLs to upload and attach to the tweet.",
    )
    tagged_users: list[list[str]] | None = Field(
        default=None,
        description="Tagged users for each media entity.",
    )
    in_reply_to_tweet_id: str | None = Field(default=None, description="Reply target tweet ID.")
    attachment_url: str | None = Field(default=None, description="Optional attached URL.")
    conversation_control: str | None = Field(
        default=None,
        description="Conversation control mode supported by Twitter.",
    )

    @model_validator(mode="after")
    def validate_media_count(self) -> "CreateTweetRequest":
        media_count = len(self.media_ids or []) + len(self.image_urls or [])
        if media_count > 4:
            raise ValueError("A tweet can include at most 4 images.")
        if any(url.scheme != "https" for url in self.image_urls or []):
            raise ValueError("Image URLs must use HTTPS.")
        return self


class CreateTweetResponse(BaseModel):
    tweet_id: str
    tweet_text: str | None = None
    raw_response: dict[str, Any]


class DeleteTweetResponse(BaseModel):
    tweet_id: str
    deleted: bool
    raw_response: dict[str, Any]


class ErrorResponse(BaseModel):
    detail: str
