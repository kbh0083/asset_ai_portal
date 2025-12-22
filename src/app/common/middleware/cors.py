"""
CORS 미들웨어 설정

로컬 및 도메인 환경 모두 지원
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings


def setup_cors(app: FastAPI) -> None:
    """
    CORS 미들웨어 설정

    Args:
        app: FastAPI 애플리케이션 인스턴스
    """
    settings = get_settings()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,  # 쿠키 전송을 위해 True
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )

