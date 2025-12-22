"""
SAML 2.0 인증

외부 IdP를 통한 SSO 인증 처리
"""

from typing import Any
from urllib.parse import urlparse

from onelogin.saml2.auth import OneLogin_Saml2_Auth
from onelogin.saml2.settings import OneLogin_Saml2_Settings
from fastapi import Request

from app.config import get_settings
from app.common.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


def get_saml_settings() -> dict[str, Any]:
    """
    SAML 설정 반환

    python3-saml 라이브러리 형식의 설정
    """
    return {
        "strict": settings.saml_strict,
        "debug": settings.saml_debug,
        "sp": {
            "entityId": settings.saml_sp_entity_id,
            "assertionConsumerService": {
                "url": settings.saml_sp_acs_url,
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST",
            },
            "singleLogoutService": {
                "url": settings.saml_sp_sls_url,
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
            },
            "NameIDFormat": "urn:oasis:names:tc:SAML:1.1:nameid-format:unspecified",
        },
        "idp": {
            "entityId": settings.saml_idp_entity_id,
            "singleSignOnService": {
                "url": settings.saml_idp_sso_url,
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
            },
            "singleLogoutService": {
                "url": settings.saml_idp_slo_url,
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
            },
            "x509cert": settings.saml_idp_x509_cert,
        },
        "security": {
            "nameIdEncrypted": False,
            "authnRequestsSigned": False,
            "logoutRequestSigned": False,
            "logoutResponseSigned": False,
            "signMetadata": False,
            "wantMessagesSigned": False,
            "wantAssertionsSigned": False,
            "wantNameIdEncrypted": False,
            "requestedAuthnContext": False,
        },
    }


def prepare_request_for_saml(request: Request) -> dict[str, Any]:
    """
    FastAPI Request를 SAML 라이브러리 형식으로 변환

    Args:
        request: FastAPI Request 객체

    Returns:
        SAML 라이브러리용 요청 딕셔너리
    """
    url = str(request.url)
    parsed = urlparse(url)

    return {
        "https": "on" if parsed.scheme == "https" else "off",
        "http_host": request.headers.get("host", parsed.netloc),
        "server_port": parsed.port or (443 if parsed.scheme == "https" else 80),
        "script_name": parsed.path,
        "get_data": dict(request.query_params),
        # POST 데이터는 별도로 처리 필요
        "post_data": {},
    }


class SAMLAuth:
    """
    SAML 인증 헬퍼

    SAML 2.0 SSO 인증 흐름 처리
    """

    def __init__(self, request: Request) -> None:
        self._request = request
        self._prepared_request = prepare_request_for_saml(request)
        self._settings = get_saml_settings()

    def _get_auth(self) -> OneLogin_Saml2_Auth:
        """OneLogin_Saml2_Auth 인스턴스 생성"""
        return OneLogin_Saml2_Auth(self._prepared_request, self._settings)

    def get_login_url(self, return_to: str | None = None) -> str:
        """
        SSO 로그인 URL 반환

        Args:
            return_to: 로그인 후 리다이렉트할 URL

        Returns:
            IdP 로그인 URL
        """
        auth = self._get_auth()
        return auth.login(return_to=return_to)

    def get_logout_url(self, return_to: str | None = None) -> str:
        """
        SSO 로그아웃 URL 반환

        Args:
            return_to: 로그아웃 후 리다이렉트할 URL

        Returns:
            IdP 로그아웃 URL
        """
        auth = self._get_auth()
        return auth.logout(return_to=return_to)

    async def process_response(self, post_data: dict[str, Any]) -> dict[str, Any] | None:
        """
        SAML 응답 처리

        Args:
            post_data: POST 요청 데이터

        Returns:
            사용자 정보 또는 None (인증 실패 시)
        """
        self._prepared_request["post_data"] = post_data
        auth = self._get_auth()

        auth.process_response()
        errors = auth.get_errors()

        if errors:
            logger.error(
                "SAML authentication failed",
                errors=errors,
                last_error_reason=auth.get_last_error_reason(),
            )
            return None

        if not auth.is_authenticated():
            logger.warning("SAML response received but not authenticated")
            return None

        # 사용자 정보 추출
        attributes = auth.get_attributes()
        name_id = auth.get_nameid()

        user_data = {
            "name_id": name_id,
            "session_index": auth.get_session_index(),
            "attributes": attributes,
        }

        logger.info("SAML authentication successful", name_id=name_id)
        return user_data

    def get_metadata(self) -> str:
        """
        SP 메타데이터 XML 반환

        IdP 등록 시 사용
        """
        saml_settings = OneLogin_Saml2_Settings(self._settings, sp_validation_only=True)
        metadata = saml_settings.get_sp_metadata()
        errors = saml_settings.validate_metadata(metadata)

        if errors:
            raise ValueError(f"Invalid SP metadata: {errors}")

        return metadata

