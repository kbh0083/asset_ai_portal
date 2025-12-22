"""
비동기 유틸리티

동기 함수를 비동기로 실행하거나,
동시성 제어를 위한 헬퍼 함수들
"""

import asyncio
from collections.abc import Awaitable, Callable, Coroutine
from concurrent.futures import ThreadPoolExecutor
from functools import partial, wraps
from typing import Any, ParamSpec, TypeVar

P = ParamSpec("P")
T = TypeVar("T")

# 기본 스레드 풀 (동기 함수 실행용)
_thread_pool: ThreadPoolExecutor | None = None


def get_thread_pool(max_workers: int = 10) -> ThreadPoolExecutor:
    """스레드 풀 반환 (싱글톤)"""
    global _thread_pool
    if _thread_pool is None:
        _thread_pool = ThreadPoolExecutor(max_workers=max_workers)
    return _thread_pool


def shutdown_thread_pool() -> None:
    """스레드 풀 종료"""
    global _thread_pool
    if _thread_pool is not None:
        _thread_pool.shutdown(wait=True)
        _thread_pool = None


async def run_in_executor(
    func: Callable[P, T],
    *args: P.args,
    **kwargs: P.kwargs,
) -> T:
    """
    동기 함수를 비동기로 실행

    블로킹 함수를 스레드 풀에서 실행하여
    이벤트 루프를 블로킹하지 않음

    Args:
        func: 동기 함수
        *args: 위치 인자
        **kwargs: 키워드 인자

    Returns:
        함수 실행 결과
    """
    loop = asyncio.get_running_loop()
    pool = get_thread_pool()

    # partial로 kwargs 바인딩
    if kwargs:
        func = partial(func, **kwargs)  # type: ignore

    return await loop.run_in_executor(pool, func, *args)


def to_async(func: Callable[P, T]) -> Callable[P, Coroutine[Any, Any, T]]:
    """
    동기 함수를 비동기 함수로 변환하는 데코레이터

    Example:
        @to_async
        def blocking_operation(x: int) -> int:
            time.sleep(1)
            return x * 2

        result = await blocking_operation(5)
    """

    @wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        return await run_in_executor(func, *args, **kwargs)

    return wrapper


async def gather_with_concurrency(
    limit: int,
    *coros: Awaitable[T],
) -> list[T]:
    """
    동시성 제한이 있는 gather

    너무 많은 비동기 작업이 동시에 실행되는 것을 방지

    Args:
        limit: 최대 동시 실행 수
        *coros: 코루틴들

    Returns:
        결과 리스트 (입력 순서 유지)
    """
    semaphore = asyncio.Semaphore(limit)

    async def limited_coro(coro: Awaitable[T]) -> T:
        async with semaphore:
            return await coro

    return await asyncio.gather(*(limited_coro(c) for c in coros))


async def gather_with_exceptions(
    *coros: Awaitable[T],
    return_exceptions: bool = True,
) -> list[T | BaseException]:
    """
    예외를 포함하여 모든 결과를 반환하는 gather

    일부 작업이 실패해도 다른 작업의 결과는 반환

    Args:
        *coros: 코루틴들
        return_exceptions: 예외를 결과에 포함할지 여부

    Returns:
        결과 또는 예외 리스트
    """
    return await asyncio.gather(*coros, return_exceptions=return_exceptions)


async def retry_async(
    func: Callable[..., Awaitable[T]],
    *args: Any,
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
    **kwargs: Any,
) -> T:
    """
    재시도 로직이 포함된 비동기 함수 실행

    Args:
        func: 비동기 함수
        *args: 위치 인자
        max_attempts: 최대 시도 횟수
        delay: 초기 대기 시간 (초)
        backoff: 백오프 배수
        exceptions: 재시도할 예외 타입들
        **kwargs: 키워드 인자

    Returns:
        함수 실행 결과

    Raises:
        마지막 시도에서 발생한 예외
    """
    last_exception: Exception | None = None
    current_delay = delay

    for attempt in range(max_attempts):
        try:
            return await func(*args, **kwargs)
        except exceptions as e:
            last_exception = e
            if attempt < max_attempts - 1:
                await asyncio.sleep(current_delay)
                current_delay *= backoff

    if last_exception is not None:
        raise last_exception
    raise RuntimeError("Unexpected error in retry_async")


class AsyncContextGroup:
    """
    여러 비동기 컨텍스트 매니저를 그룹으로 관리

    Example:
        async with AsyncContextGroup() as group:
            db = await group.enter(get_db_session())
            cache = await group.enter(get_cache_client())
            # 모든 컨텍스트가 자동으로 종료됨
    """

    def __init__(self) -> None:
        self._stack: list[Any] = []

    async def __aenter__(self) -> "AsyncContextGroup":
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        # 역순으로 종료
        for ctx in reversed(self._stack):
            await ctx.__aexit__(exc_type, exc_val, exc_tb)

    async def enter(self, ctx: Any) -> Any:
        """컨텍스트 매니저 진입"""
        result = await ctx.__aenter__()
        self._stack.append(ctx)
        return result

