from typing import Any

from pydantic import BaseModel, Field


class CreateTweetRequest(BaseModel):
    tweet_text: str = Field(..., min_length=1, description="Tweet body.")
    media_ids: list[str] | None = Field(default=None, description="Optional media IDs.")
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
