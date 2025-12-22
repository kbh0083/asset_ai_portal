"""
커스텀 예외 클래스

HTTP 상태 코드와 매핑되는 애플리케이션 예외
"""

from typing import Any


class AppException(Exception):
    """
    애플리케이션 기본 예외

    모든 커스텀 예외의 베이스 클래스
    """

    status_code: int = 500
    error_code: str = "INTERNAL_ERROR"
    message: str = "An unexpected error occurred"

    def __init__(
        self,
        message: str | None = None,
        error_code: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.message = message or self.message
        self.error_code = error_code or self.error_code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> dict[str, Any]:
        """예외를 딕셔너리로 변환"""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
        }


class BadRequestError(AppException):
    """400 Bad Request"""

    status_code = 400
    error_code = "BAD_REQUEST"
    message = "Invalid request"


class UnauthorizedError(AppException):
    """401 Unauthorized"""

    status_code = 401
    error_code = "UNAUTHORIZED"
    message = "Authentication required"


class ForbiddenError(AppException):
    """403 Forbidden"""

    status_code = 403
    error_code = "FORBIDDEN"
    message = "Access denied"


class NotFoundError(AppException):
    """404 Not Found"""

    status_code = 404
    error_code = "NOT_FOUND"
    message = "Resource not found"


class ConflictError(AppException):
    """409 Conflict"""

    status_code = 409
    error_code = "CONFLICT"
    message = "Resource conflict"


class ValidationError(AppException):
    """422 Unprocessable Entity"""

    status_code = 422
    error_code = "VALIDATION_ERROR"
    message = "Validation failed"


class InternalServerError(AppException):
    """500 Internal Server Error"""

    status_code = 500
    error_code = "INTERNAL_ERROR"
    message = "Internal server error"


# === 도메인 특화 예외 ===


class LLMError(AppException):
    """LLM 관련 예외"""

    status_code = 503
    error_code = "LLM_ERROR"
    message = "LLM service error"


class CrawlerError(AppException):
    """크롤러 관련 예외"""

    status_code = 503
    error_code = "CRAWLER_ERROR"
    message = "Crawler service error"


class ExternalServiceError(AppException):
    """외부 서비스 관련 예외"""

    status_code = 503
    error_code = "EXTERNAL_SERVICE_ERROR"
    message = "External service error"


class RateLimitError(AppException):
    """429 Too Many Requests"""

    status_code = 429
    error_code = "RATE_LIMIT_EXCEEDED"
    message = "Rate limit exceeded"

