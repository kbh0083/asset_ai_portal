"""
Redis 비동기 클라이언트

세션 저장, 캐싱, 분산 락 등에 사용
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

import redis.asyncio as redis
from redis.asyncio import ConnectionPool, Redis

from app.config import get_settings

settings = get_settings()

# 글로벌 커넥션 풀
_pool: ConnectionPool | None = None


async def create_redis_pool() -> ConnectionPool:
    """Redis 커넥션 풀 생성"""
    return ConnectionPool.from_url(
        settings.redis_url,
        password=settings.redis_password if settings.redis_password else None,
        max_connections=settings.redis_max_connections,
        decode_responses=True,  # 자동 디코딩
        encoding="utf-8",
    )


async def get_redis_pool() -> ConnectionPool:
    """Redis 커넥션 풀 반환 (싱글톤)"""
    global _pool
    if _pool is None:
        _pool = await create_redis_pool()
    return _pool


async def close_redis_pool() -> None:
    """Redis 커넥션 풀 종료"""
    global _pool
    if _pool is not None:
        await _pool.disconnect()
        _pool = None


class RedisClient:
    """
    Redis 비동기 클라이언트 래퍼

    일반적인 캐시 작업을 위한 헬퍼 메서드 제공
    """

    def __init__(self, client: Redis) -> None:
        self._client = client

    @property
    def client(self) -> Redis:
        """원본 Redis 클라이언트 반환"""
        return self._client

    # === 기본 작업 ===

    async def get(self, key: str) -> str | None:
        """값 조회"""
        return await self._client.get(key)

    async def set(
        self,
        key: str,
        value: str | bytes | int | float,
        ex: int | None = None,  # 만료 시간 (초)
        px: int | None = None,  # 만료 시간 (밀리초)
        nx: bool = False,  # 키가 없을 때만 설정
        xx: bool = False,  # 키가 있을 때만 설정
    ) -> bool:
        """값 설정"""
        result = await self._client.set(key, value, ex=ex, px=px, nx=nx, xx=xx)
        return result is True

    async def delete(self, *keys: str) -> int:
        """키 삭제"""
        return await self._client.delete(*keys)

    async def exists(self, *keys: str) -> int:
        """키 존재 여부 확인"""
        return await self._client.exists(*keys)

    async def expire(self, key: str, seconds: int) -> bool:
        """키 만료 시간 설정"""
        return await self._client.expire(key, seconds)

    async def ttl(self, key: str) -> int:
        """키 남은 만료 시간 조회 (초)"""
        return await self._client.ttl(key)

    # === JSON 작업 (orjson 사용) ===

    async def get_json(self, key: str) -> Any | None:
        """JSON 값 조회"""
        import orjson

        value = await self._client.get(key)
        if value is None:
            return None
        return orjson.loads(value)

    async def set_json(
        self,
        key: str,
        value: Any,
        ex: int | None = None,
    ) -> bool:
        """JSON 값 설정"""
        import orjson

        json_str = orjson.dumps(value).decode("utf-8")
        return await self.set(key, json_str, ex=ex)

    # === Hash 작업 ===

    async def hget(self, name: str, key: str) -> str | None:
        """Hash 필드 조회"""
        return await self._client.hget(name, key)

    async def hset(self, name: str, key: str, value: str) -> int:
        """Hash 필드 설정"""
        return await self._client.hset(name, key, value)

    async def hgetall(self, name: str) -> dict[str, str]:
        """Hash 전체 조회"""
        return await self._client.hgetall(name)

    async def hdel(self, name: str, *keys: str) -> int:
        """Hash 필드 삭제"""
        return await self._client.hdel(name, *keys)

    # === 분산 락 ===

    @asynccontextmanager
    async def lock(
        self,
        name: str,
        timeout: float = 10.0,
        blocking: bool = True,
        blocking_timeout: float = 10.0,
    ) -> AsyncGenerator[redis.lock.Lock, None]:
        """
        분산 락 컨텍스트 매니저

        Args:
            name: 락 이름
            timeout: 락 자동 해제 시간 (초)
            blocking: 락 획득까지 대기 여부
            blocking_timeout: 락 대기 최대 시간 (초)

        Yields:
            Lock: Redis 락 객체
        """
        lock = self._client.lock(
            name,
            timeout=timeout,
            blocking=blocking,
            blocking_timeout=blocking_timeout,
        )
        try:
            await lock.acquire()
            yield lock
        finally:
            await lock.release()

    # === Pub/Sub ===

    async def publish(self, channel: str, message: str) -> int:
        """메시지 발행"""
        return await self._client.publish(channel, message)


async def get_redis_client() -> AsyncGenerator[RedisClient, None]:
    """
    Redis 클라이언트 의존성

    FastAPI Depends에서 사용

    Yields:
        RedisClient: Redis 클라이언트 래퍼
    """
    pool = await get_redis_pool()
    client = Redis(connection_pool=pool)
    try:
        yield RedisClient(client)
    finally:
        await client.aclose()

