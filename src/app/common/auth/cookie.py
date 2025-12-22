"""
쿠키 관리

로컬/도메인 환경 모두 지원하는 쿠키 설정
"""

from fastapi import Response

from app.config import get_settings

settings = get_settings()


class CookieManager:
    """
    쿠키 관리자

    세션 쿠키 설정/삭제를 담당
    로컬(localhost)과 도메인 환경 모두 지원
    """

    def __init__(self) -> None:
        self._cookie_name = settings.session_cookie_name
        self._max_age = settings.session_cookie_max_age
        self._secure = settings.session_cookie_secure
        self._httponly = settings.session_cookie_httponly
        self._samesite = settings.session_cookie_samesite

    def set_session_cookie(
        self,
        response: Response,
        session_id: str,
        max_age: int | None = None,
    ) -> None:
        """
        세션 쿠키 설정

        Args:
            response: FastAPI Response 객체
            session_id: 세션 ID
            max_age: 쿠키 만료 시간 (초)
        """
        response.set_cookie(
            key=self._cookie_name,
            value=session_id,
            max_age=max_age or self._max_age,
            path="/",
            # domain은 설정하지 않음 (현재 도메인에만 적용)
            # 로컬 환경에서도 동작하도록
            secure=self._secure,
            httponly=self._httponly,
            samesite=self._samesite,
        )

    def delete_session_cookie(self, response: Response) -> None:
        """
        세션 쿠키 삭제

        Args:
            response: FastAPI Response 객체
        """
        response.delete_cookie(
            key=self._cookie_name,
            path="/",
            secure=self._secure,
            httponly=self._httponly,
            samesite=self._samesite,
        )

    def get_cookie_options(self) -> dict:
        """
        현재 쿠키 설정 반환 (디버깅용)
        """
        return {
            "name": self._cookie_name,
            "max_age": self._max_age,
            "secure": self._secure,
            "httponly": self._httponly,
            "samesite": self._samesite,
        }


# 싱글톤 인스턴스
_cookie_manager: CookieManager | None = None


def get_cookie_manager() -> CookieManager:
    """쿠키 관리자 반환"""
    global _cookie_manager
    if _cookie_manager is None:
        _cookie_manager = CookieManager()
    return _cookie_manager

