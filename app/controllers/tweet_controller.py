from fastapi import APIRouter, Depends, status

from app.dependencies import get_tweet_service
from app.schemas.tweet import CreateTweetRequest, CreateTweetResponse, DeleteTweetResponse
from app.services.tweet_service import TweetService

router = APIRouter(prefix="/tweets", tags=["tweets"])


@router.post("", response_model=CreateTweetResponse, status_code=status.HTTP_201_CREATED)
def create_tweet(
    payload: CreateTweetRequest,
    tweet_service: TweetService = Depends(get_tweet_service),
) -> CreateTweetResponse:
    return tweet_service.create_tweet(payload)


@router.delete("/{tweet_id}", response_model=DeleteTweetResponse, status_code=status.HTTP_200_OK)
def delete_tweet(
    tweet_id: str,
    tweet_service: TweetService = Depends(get_tweet_service),
) -> DeleteTweetResponse:
    return tweet_service.delete_tweet(tweet_id)
