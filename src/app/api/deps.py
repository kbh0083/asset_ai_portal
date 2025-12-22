"""
API 의존성

공통으로 사용되는 의존성 모음
"""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.infrastructure.database import get_async_session
from app.common.infrastructure.cache import RedisClient, get_redis_client
from app.common.auth import CurrentUser, get_current_user, get_current_user_optional

# 타입 힌트 별칭 (라우터에서 사용)
AsyncSessionDep = Annotated[AsyncSession, Depends(get_async_session)]
RedisDep = Annotated[RedisClient, Depends(get_redis_client)]
CurrentUserDep = Annotated[CurrentUser, Depends(get_current_user)]
OptionalUserDep = Annotated[CurrentUser | None, Depends(get_current_user_optional)]
