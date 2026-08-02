"""Maps provider-adapter exceptions onto HTTP responses, so routers can call provider code
without repeating try/except boilerplate."""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.providers.base import (
    ProviderAuthenticationError,
    ProviderError,
    ProviderInvalidTrackingNumberError,
    ProviderNotConfiguredError,
    ProviderRateLimitedError,
)

_STATUS_BY_EXCEPTION: list[tuple[type[ProviderError], int]] = [
    (ProviderInvalidTrackingNumberError, status.HTTP_404_NOT_FOUND),
    (ProviderNotConfiguredError, status.HTTP_409_CONFLICT),
    (ProviderRateLimitedError, status.HTTP_429_TOO_MANY_REQUESTS),
    (ProviderAuthenticationError, status.HTTP_424_FAILED_DEPENDENCY),
]


def _status_for(exc: ProviderError) -> int:
    for exc_type, http_status in _STATUS_BY_EXCEPTION:
        if isinstance(exc, exc_type):
            return http_status
    return status.HTTP_502_BAD_GATEWAY


async def _handle_provider_error(request: Request, exc: Exception) -> JSONResponse:
    # Only ever registered for ProviderError (see register_exception_handlers below); Starlette's
    # add_exception_handler is typed against the broader Exception, hence the narrowing here.
    assert isinstance(exc, ProviderError)
    return JSONResponse(status_code=_status_for(exc), content={"detail": str(exc)})


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(ProviderError, _handle_provider_error)
