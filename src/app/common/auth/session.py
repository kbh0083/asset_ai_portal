"""
세션 관리

Redis 기반 분산 세션 저장소
"""

import secrets
from datetime import timedelta
from typing import Any

from app.config import get_settings
from app.common.infrastructure.cache import RedisClient, get_redis_client
from app.common.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

# 세션 키 프리픽스
SESSION_PREFIX = "session:"


class SessionManager:
    """
    세션 관리자

    Redis를 사용한 분산 세션 관리
    """

    def __init__(self, redis_client: RedisClient) -> None:
        self._redis = redis_client
        self._max_age = settings.session_cookie_max_age

    def _get_session_key(self, session_id: str) -> str:
        """세션 키 생성"""
        return f"{SESSION_PREFIX}{session_id}"

    @staticmethod
    def generate_session_id() -> str:
        """안전한 세션 ID 생성"""
        return secrets.token_urlsafe(32)

    async def create_session(
        self,
        user_id: str,
        user_data: dict[str, Any],
        ttl: int | None = None,
    ) -> str:
        """
        새 세션 생성

        Args:
            user_id: 사용자 ID
            user_data: 세션에 저장할 사용자 데이터
            ttl: 세션 만료 시간 (초), None이면 기본값 사용

        Returns:
            세션 ID
        """
        session_id = self.generate_session_id()
        session_key = self._get_session_key(session_id)

        session_data = {
            "user_id": user_id,
            "data": user_data,
        }

        ttl = ttl or self._max_age
        await self._redis.set_json(session_key, session_data, ex=ttl)

        logger.info("Session created", session_id=session_id[:8], user_id=user_id)
        return session_id

    async def get_session(self, session_id: str) -> dict[str, Any] | None:
        """
        세션 조회

        Args:
            session_id: 세션 ID

        Returns:
            세션 데이터 또는 None
        """
        session_key = self._get_session_key(session_id)
        session_data = await self._redis.get_json(session_key)

        if session_data is None:
            logger.debug("Session not found", session_id=session_id[:8])
            return None

        return session_data

    async def update_session(
        self,
        session_id: str,
        user_data: dict[str, Any],
    ) -> bool:
        """
        세션 데이터 업데이트

        Args:
            session_id: 세션 ID
            user_data: 업데이트할 사용자 데이터

        Returns:
            성공 여부
        """
        session_key = self._get_session_key(session_id)
        session_data = await self._redis.get_json(session_key)

        if session_data is None:
            return False

        # 기존 TTL 유지
        ttl = await self._redis.ttl(session_key)
        if ttl < 0:
            ttl = self._max_age

        session_data["data"].update(user_data)
        await self._redis.set_json(session_key, session_data, ex=ttl)

        logger.debug("Session updated", session_id=session_id[:8])
        return True

    async def refresh_session(self, session_id: str) -> bool:
        """
        세션 만료 시간 갱신

        Args:
            session_id: 세션 ID

        Returns:
            성공 여부
        """
        session_key = self._get_session_key(session_id)
        exists = await self._redis.exists(session_key)

        if not exists:
            return False

        await self._redis.expire(session_key, self._max_age)
        logger.debug("Session refreshed", session_id=session_id[:8])
        return True

    async def delete_session(self, session_id: str) -> bool:
        """
        세션 삭제

        Args:
            session_id: 세션 ID

        Returns:
            성공 여부
        """
        session_key = self._get_session_key(session_id)
        deleted = await self._redis.delete(session_key)

        if deleted > 0:
            logger.info("Session deleted", session_id=session_id[:8])
            return True
        return False

    async def delete_user_sessions(self, user_id: str) -> int:
        """
        사용자의 모든 세션 삭제

        Args:
            user_id: 사용자 ID

        Returns:
            삭제된 세션 수
        """
        # TODO: 사용자별 세션 목록 관리 필요
        # 현재는 개별 세션 삭제로 대체
        logger.info("User sessions deletion requested", user_id=user_id)
        return 0


async def get_session_manager() -> SessionManager:
    """
    세션 매니저 의존성

    FastAPI Depends에서 사용
    """
    async for redis_client in get_redis_client():
        return SessionManager(redis_client)
    raise RuntimeError("Failed to get Redis client")

