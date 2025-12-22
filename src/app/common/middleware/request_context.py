"""
요청 컨텍스트 미들웨어

요청별 고유 ID 생성 및 로깅 컨텍스트 설정
"""

import uuid
from collections.abc import Callable
from typing import Awaitable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.common.logging import bind_request_context, clear_request_context, get_logger

logger = get_logger(__name__)


class RequestContextMiddleware(BaseHTTPMiddleware):
    """
    요청 컨텍스트 미들웨어

    - 요청별 고유 ID 생성
    - 로깅 컨텍스트에 요청 정보 바인딩
    - 응답 헤더에 요청 ID 추가
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        # 요청 ID 생성 (헤더에서 가져오거나 새로 생성)
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

        # 요청 컨텍스트 설정
        request.state.request_id = request_id

        # 로깅 컨텍스트 바인딩
        bind_request_context(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            client_ip=self._get_client_ip(request),
        )

        logger.info(
            "Request started",
            query_params=str(request.query_params),
        )

        try:
            response = await call_next(request)

            logger.info(
                "Request completed",
                status_code=response.status_code,
            )

            # 응답 헤더에 요청 ID 추가
            response.headers["X-Request-ID"] = request_id
            return response

        except Exception as e:
            logger.exception("Request failed", error=str(e))
            raise

        finally:
            # 컨텍스트 정리
            clear_request_context()

    @staticmethod
    def _get_client_ip(request: Request) -> str:
        """클라이언트 IP 추출 (프록시 환경 지원)"""
        # X-Forwarded-For 헤더 확인 (프록시/로드밸런서 환경)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # 첫 번째 IP가 실제 클라이언트 IP
            return forwarded_for.split(",")[0].strip()

        # X-Real-IP 헤더 확인 (Nginx 등)
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # 직접 연결된 클라이언트 IP
        if request.client:
            return request.client.host

        return "unknown"

