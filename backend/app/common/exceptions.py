"""Application exception hierarchy + FastAPI handlers (U0).

Units raise typed ``AppError`` subclasses; the central handlers translate them
to a standard ``ErrorResponse`` (BR-U0-10).
"""
from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.common.schemas import ErrorResponse


class AppError(Exception):
    """Base application error."""

    status_code: int = 400
    error_code: str = "app_error"

    def __init__(self, detail: str | None = None):
        self.detail = detail
        super().__init__(detail or self.error_code)


class ValidationError(AppError):
    status_code = 422
    error_code = "validation_error"


class NotFoundError(AppError):
    status_code = 404
    error_code = "not_found"


class ForbiddenError(AppError):
    status_code = 403
    error_code = "forbidden"


class AuthError(AppError):
    status_code = 401
    error_code = "unauthorized"


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _handle_app_error(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(error=exc.error_code, detail=exc.detail).model_dump(),
        )
