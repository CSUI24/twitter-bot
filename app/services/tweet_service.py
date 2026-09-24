from typing import TYPE_CHECKING

from app.core.config import get_settings
from app.core.exceptions import TwitterConfigurationError, TwitterServiceError
from app.schemas.tweet import CreateTweetRequest, CreateTweetResponse, DeleteTweetResponse
from app.services.media_upload import TwitterMediaUploader

if TYPE_CHECKING:
    from app.services.twitter_client import TwitterClientProvider


class TweetService:
    def __init__(self, client_provider: "TwitterClientProvider") -> None:
        self.client_provider = client_provider

    def create_tweet(self, payload: CreateTweetRequest) -> CreateTweetResponse:
        try:
            media_ids = list(payload.media_ids or [])
            media_ids.extend(
                TwitterMediaUploader(
                    get_settings(),
                    self.client_provider,
                ).upload_images(
                    [str(url) for url in payload.image_urls or []],
                    existing_media_count=len(payload.media_ids or []),
                )
            )
            response = self.client_provider.get_client().get_post_api().post_create_tweet(
                tweet_text=payload.tweet_text,
                media_ids=media_ids or None,
                tagged_users=payload.tagged_users,
                in_reply_to_tweet_id=payload.in_reply_to_tweet_id,
                attachment_url=payload.attachment_url,
                conversation_control=payload.conversation_control,
            )
        except (TwitterConfigurationError, TwitterServiceError):
            raise
        except Exception as exc:
            raise TwitterServiceError(f"Failed to create tweet: {exc}") from exc

        result = response.data.data.create_tweet
        if result is None or result.tweet_results.result is None:
            raise TwitterServiceError("Twitter did not return a created tweet payload.")

        tweet = result.tweet_results.result
        tweet_text = tweet.legacy.full_text if tweet.legacy is not None else None

        return CreateTweetResponse(
            tweet_id=tweet.rest_id,
            tweet_text=tweet_text,
            raw_response=response.data.to_dict(),
        )

    def delete_tweet(self, tweet_id: str) -> DeleteTweetResponse:
        try:
            response = self.client_provider.get_client().get_post_api().post_delete_tweet(tweet_id=tweet_id)
        except Exception as exc:
            raise TwitterServiceError(f"Failed to delete tweet {tweet_id}: {exc}") from exc

        print(response)

        return DeleteTweetResponse(
            tweet_id=tweet_id,
            deleted=True,
            raw_response=response.data.to_dict(),
        )
