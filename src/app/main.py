"""
FastAPI 애플리케이션 진입점

Samsung AI Portal 메인 애플리케이션
"""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

from app.config import get_settings
from app.config.constants import API_V1_PREFIX
from app.common.logging import setup_logging, get_logger
from app.common.middleware import setup_cors, RequestContextMiddleware
from app.common.exceptions import setup_exception_handlers
from app.common.infrastructure.database.session import init_db, close_db
from app.common.infrastructure.cache.redis import close_redis_pool
from app.api.v1.router import api_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """애플리케이션 생명주기 관리"""
    # === 시작 ===
    setup_logging()
    logger = get_logger(__name__)
    logger.info("Application starting", app_name=settings.app_name, env=settings.app_env)

    # 개발 환경에서만 테이블 자동 생성
    if settings.is_development:
        await init_db()
        logger.info("Database initialized (development mode)")

    yield

    # === 종료 ===
    logger.info("Application shutting down")
    await close_db()
    await close_redis_pool()


def create_app() -> FastAPI:
    """FastAPI 애플리케이션 팩토리"""
    app = FastAPI(
        title="Samsung AI Portal",
        description="삼성자산운용 AI 서비스 플랫폼",
        version="0.1.0",
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
        openapi_url="/openapi.json" if settings.is_development else None,
        default_response_class=ORJSONResponse,
        lifespan=lifespan,
    )

    # 미들웨어 설정
    setup_cors(app)
    app.add_middleware(RequestContextMiddleware)

    # 예외 핸들러 설정
    setup_exception_handlers(app)

    # API 라우터 등록
    app.include_router(api_router, prefix=API_V1_PREFIX)

    # 헬스체크
    @app.get("/health")
    async def health_check() -> dict[str, str]:
        return {"status": "healthy"}

    @app.get("/")
    async def root() -> dict[str, str]:
        return {
            "name": "Samsung AI Portal",
            "version": "0.1.0",
        }

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.is_development,
    )
