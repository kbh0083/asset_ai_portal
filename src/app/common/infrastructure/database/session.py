"""
비동기 데이터베이스 세션 관리

asyncpg를 사용한 PostgreSQL 비동기 연결
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.config import get_settings

settings = get_settings()

# 비동기 엔진 생성
# - pool_pre_ping: 커넥션 유효성 검사
# - pool_recycle: 커넥션 재활용 시간 (1시간)
async_engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    pool_timeout=settings.database_pool_timeout,
    pool_recycle=3600,
)

# 테스트용 엔진 (NullPool 사용)
async_engine_test = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    poolclass=NullPool,
)

# 비동기 세션 팩토리
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    비동기 세션 의존성

    FastAPI Depends에서 사용
    세션은 자동으로 커밋/롤백되지 않으며,
    서비스 레이어에서 명시적으로 처리해야 함

    Yields:
        AsyncSession: 비동기 데이터베이스 세션
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    데이터베이스 초기화

    테이블 생성 (개발 환경에서만 사용)
    운영 환경에서는 Alembic 마이그레이션 사용
    """
    from app.common.infrastructure.database.base import Base

    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """데이터베이스 연결 종료"""
    await async_engine.dispose()

