"""
인증 의존성

FastAPI Depends에서 사용하는 인증 관련 의존성
"""

from collections.abc import Callable
from typing import Any

from fastapi import Cookie, Depends, HTTPException, status

from app.config import get_settings
from app.common.auth.session import SessionManager, get_session_manager
from app.common.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class CurrentUser:
    """
    현재 인증된 사용자 정보

    세션에서 추출한 사용자 데이터를 담는 객체
    """

    def __init__(
        self,
        user_id: str,
        session_id: str,
        data: dict[str, Any],
    ) -> None:
        self.user_id = user_id
        self.session_id = session_id
        self._data = data

    @property
    def email(self) -> str | None:
        """사용자 이메일"""
        return self._data.get("email")

    @property
    def name(self) -> str | None:
        """사용자 이름"""
        return self._data.get("name")

    @property
    def roles(self) -> list[str]:
        """사용자 역할 목록"""
        return self._data.get("roles", [])

    @property
    def attributes(self) -> dict[str, Any]:
        """SAML 속성"""
        return self._data.get("attributes", {})

    def has_role(self, role: str) -> bool:
        """특정 역할 보유 여부"""
        return role in self.roles

    def has_any_role(self, *roles: str) -> bool:
        """주어진 역할 중 하나라도 보유 여부"""
        return any(self.has_role(role) for role in roles)

    def to_dict(self) -> dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "user_id": self.user_id,
            "email": self.email,
            "name": self.name,
            "roles": self.roles,
        }


def _get_mock_user() -> CurrentUser:
    """
    모킹 사용자 반환 (개발용)

    AUTH_MOCK_ENABLED=true 일 때 사용
    """
    return CurrentUser(
        user_id=settings.auth_mock_user_id,
        session_id="mock-session",
        data={
            "email": settings.auth_mock_user_email,
            "name": settings.auth_mock_user_name,
            "roles": settings.auth_mock_user_roles,
        },
    )


async def get_current_user(
    session_id: str | None = Cookie(None, alias=settings.session_cookie_name),
    session_manager: SessionManager = Depends(get_session_manager),
) -> CurrentUser:
    """
    현재 인증된 사용자 반환

    세션 쿠키로부터 사용자 정보를 추출
    인증되지 않은 경우 401 에러 발생

    AUTH_MOCK_ENABLED=true 인 경우 모킹 사용자 반환

    Raises:
        HTTPException: 인증되지 않은 경우
    """
    # Mock 모드: 더미 사용자 반환
    if settings.auth_mock_enabled:
        logger.debug("Auth mock enabled, returning mock user")
        return _get_mock_user()

    if not session_id:
        logger.debug("No session cookie found")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    session_data = await session_manager.get_session(session_id)

    if not session_data:
        logger.debug("Session not found or expired", session_id=session_id[:8])
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or invalid",
        )

    # 세션 갱신 (슬라이딩 세션)
    await session_manager.refresh_session(session_id)

    return CurrentUser(
        user_id=session_data["user_id"],
        session_id=session_id,
        data=session_data.get("data", {}),
    )


async def get_current_user_optional(
    session_id: str | None = Cookie(None, alias=settings.session_cookie_name),
    session_manager: SessionManager = Depends(get_session_manager),
) -> CurrentUser | None:
    """
    현재 사용자 반환 (인증 선택적)

    인증되지 않은 경우 None 반환
    AUTH_MOCK_ENABLED=true 인 경우 모킹 사용자 반환
    """
    # Mock 모드: 더미 사용자 반환
    if settings.auth_mock_enabled:
        return _get_mock_user()

    if not session_id:
        return None

    session_data = await session_manager.get_session(session_id)

    if not session_data:
        return None

    # 세션 갱신
    await session_manager.refresh_session(session_id)

    return CurrentUser(
        user_id=session_data["user_id"],
        session_id=session_id,
        data=session_data.get("data", {}),
    )


def require_roles(*required_roles: str) -> Callable:
    """
    역할 기반 접근 제어 의존성 팩토리

    Args:
        *required_roles: 필요한 역할 목록 (하나라도 있으면 접근 허용)

    Returns:
        FastAPI 의존성 함수

    Example:
        @router.get("/admin")
        async def admin_only(
            user: CurrentUser = Depends(require_roles("admin", "superuser"))
        ):
            ...
    """

    async def role_checker(
        user: CurrentUser = Depends(get_current_user),
    ) -> CurrentUser:
        if not user.has_any_role(*required_roles):
            logger.warning(
                "Access denied - insufficient roles",
                user_id=user.user_id,
                required_roles=required_roles,
                user_roles=user.roles,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return user

    return role_checker

