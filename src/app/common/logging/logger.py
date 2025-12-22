"""
구조화된 로깅 설정 (structlog 기반)

비동기 환경에서도 안전하게 동작하며,
JSON 또는 콘솔 포맷으로 출력 가능
"""

import logging
import sys
from typing import Any

import structlog
from structlog.types import Processor

from app.config import get_settings


def setup_logging() -> None:
    """
    애플리케이션 로깅 초기화

    환경에 따라 JSON 또는 콘솔 포맷으로 설정
    """
    settings = get_settings()

    # 공통 프로세서
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    # 환경별 렌더러 설정
    if settings.log_format == "json":
        # JSON 포맷 (운영 환경)
        renderer: Processor = structlog.processors.JSONRenderer()
    else:
        # 콘솔 포맷 (개발 환경)
        renderer = structlog.dev.ConsoleRenderer(
            colors=True,
            exception_formatter=structlog.dev.plain_traceback,
        )

    # structlog 설정
    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # stdlib logging 핸들러 설정
    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    # 루트 로거 설정
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level))

    # 기존 핸들러 제거
    root_logger.handlers.clear()

    # 콘솔 핸들러
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # 파일 핸들러 (설정된 경우)
    if settings.log_file_path:
        from pathlib import Path

        log_path = Path(settings.log_file_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # 외부 라이브러리 로깅 레벨 조정
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.DEBUG if settings.debug else logging.WARNING
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """
    구조화된 로거 반환

    Args:
        name: 로거 이름 (기본값: 호출 모듈명)

    Returns:
        BoundLogger: structlog 바운드 로거
    """
    return structlog.get_logger(name)


class LoggerAdapter:
    """
    로깅 어댑터

    컨텍스트 정보를 쉽게 바인딩할 수 있는 래퍼
    """

    def __init__(self, name: str | None = None) -> None:
        self._logger = get_logger(name)

    def bind(self, **kwargs: Any) -> "LoggerAdapter":
        """컨텍스트 바인딩"""
        self._logger = self._logger.bind(**kwargs)
        return self

    def unbind(self, *keys: str) -> "LoggerAdapter":
        """컨텍스트 언바인딩"""
        self._logger = self._logger.unbind(*keys)
        return self

    def debug(self, msg: str, **kwargs: Any) -> None:
        """디버그 로그"""
        self._logger.debug(msg, **kwargs)

    def info(self, msg: str, **kwargs: Any) -> None:
        """정보 로그"""
        self._logger.info(msg, **kwargs)

    def warning(self, msg: str, **kwargs: Any) -> None:
        """경고 로그"""
        self._logger.warning(msg, **kwargs)

    def error(self, msg: str, **kwargs: Any) -> None:
        """에러 로그"""
        self._logger.error(msg, **kwargs)

    def critical(self, msg: str, **kwargs: Any) -> None:
        """치명적 에러 로그"""
        self._logger.critical(msg, **kwargs)

    def exception(self, msg: str, **kwargs: Any) -> None:
        """예외 로그 (스택 트레이스 포함)"""
        self._logger.exception(msg, **kwargs)


# 요청 컨텍스트 관리
def bind_request_context(
    request_id: str,
    user_id: str | None = None,
    **extra: Any,
) -> None:
    """
    요청 컨텍스트 바인딩

    FastAPI 미들웨어에서 호출하여 요청별 컨텍스트 설정

    Args:
        request_id: 요청 ID
        user_id: 사용자 ID (인증된 경우)
        **extra: 추가 컨텍스트
    """
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        request_id=request_id,
        user_id=user_id,
        **extra,
    )


def clear_request_context() -> None:
    """요청 컨텍스트 초기화"""
    structlog.contextvars.clear_contextvars()

