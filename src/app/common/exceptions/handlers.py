"""
전역 예외 핸들러

FastAPI 앱에 등록되는 예외 핸들러들
"""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import ORJSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.common.exceptions.base import AppException
from app.common.logging import get_logger

logger = get_logger(__name__)


async def app_exception_handler(
    request: Request,
    exc: AppException,
) -> ORJSONResponse:
    """애플리케이션 예외 핸들러"""
    logger.warning(
        "Application error",
        error_code=exc.error_code,
        message=exc.message,
        details=exc.details,
        path=str(request.url.path),
    )
    return ORJSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict(),
    )


async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
) -> ORJSONResponse:
    """HTTP 예외 핸들러"""
    logger.warning(
        "HTTP error",
        status_code=exc.status_code,
        detail=exc.detail,
        path=str(request.url.path),
    )
    return ORJSONResponse(
        status_code=exc.status_code,
        content={
            "error_code": "HTTP_ERROR",
            "message": str(exc.detail),
            "details": {},
        },
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> ORJSONResponse:
    """Pydantic 유효성 검사 예외 핸들러"""
    errors = exc.errors()
    logger.warning(
        "Validation error",
        errors=errors,
        path=str(request.url.path),
    )
    return ORJSONResponse(
        status_code=422,
        content={
            "error_code": "VALIDATION_ERROR",
            "message": "Request validation failed",
            "details": {"errors": errors},
        },
    )


async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> ORJSONResponse:
    """처리되지 않은 예외 핸들러"""
    logger.exception(
        "Unhandled error",
        error_type=type(exc).__name__,
        error_message=str(exc),
        path=str(request.url.path),
    )
    return ORJSONResponse(
        status_code=500,
        content={
            "error_code": "INTERNAL_ERROR",
            "message": "An unexpected error occurred",
            "details": {},
        },
    )


def setup_exception_handlers(app: FastAPI) -> None:
    """
    FastAPI 앱에 예외 핸들러 등록

    Args:
        app: FastAPI 애플리케이션 인스턴스
    """
    app.add_exception_handler(AppException, app_exception_handler)  # type: ignore
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)  # type: ignore
    app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore
    app.add_exception_handler(Exception, unhandled_exception_handler)

