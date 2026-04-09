from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.controllers.tweet_controller import router as tweet_router
from app.core.config import get_settings
from app.core.exceptions import TwitterConfigurationError, TwitterServiceError
from app.schemas.tweet import ErrorResponse


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        description="FastAPI service for creating and deleting tweets.",
    )

    @app.exception_handler(TwitterConfigurationError)
    async def handle_configuration_error(
        request: Request,
        exc: TwitterConfigurationError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(detail=str(exc)).model_dump(),
        )

    @app.exception_handler(TwitterServiceError)
    async def handle_twitter_service_error(
        request: Request,
        exc: TwitterServiceError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(detail=exc.message).model_dump(),
        )

    @app.get("/health", tags=["health"])
    async def health_check() -> dict[str, str]:
        return {"status": "ok", "service": "twitter"}

    app.include_router(tweet_router, prefix="/api/v1")
    return app


app = create_app()
