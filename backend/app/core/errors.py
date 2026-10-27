"""One error hierarchy, rendered everywhere as {code, message}."""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


class AppError(Exception):
    code = "internal"
    status = 500
    # Worker tasks retry only errors that may succeed on a second attempt.
    retryable = False

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class InvalidPdf(AppError):
    code = "invalid_pdf"
    status = 422


class NotFound(AppError):
    code = "not_found"
    status = 404


class Unauthorized(AppError):
    code = "unauthorized"
    status = 401


class EmailTaken(AppError):
    code = "email_taken"
    status = 409


class RateLimited(AppError):
    code = "rate_limited"
    status = 429


class LLMUnavailable(AppError):
    code = "llm_unavailable"
    status = 503

    def __init__(self, message: str, retryable: bool = True):
        super().__init__(message)
        self.retryable = retryable


class QueueUnavailable(AppError):
    code = "queue_unavailable"
    status = 503


def _error(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"code": code, "message": message})


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error(_: Request, exc: AppError) -> JSONResponse:
        return _error(exc.status, exc.code, exc.message)

    @app.exception_handler(RequestValidationError)
    async def validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        first = exc.errors()[0]
        field = ".".join(str(p) for p in first["loc"] if p != "body")
        message = f"{field}: {first['msg']}" if field else first["msg"]
        return _error(422, "validation_error", message)

    @app.exception_handler(StarletteHTTPException)
    async def http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = "not_found" if exc.status_code == 404 else "http_error"
        return _error(exc.status_code, code, str(exc.detail))

    @app.exception_handler(Exception)
    async def unhandled(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("unhandled error")
        return _error(500, "internal", "Something went wrong. Please try again.")
