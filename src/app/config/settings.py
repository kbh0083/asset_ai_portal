"""
애플리케이션 설정

환경변수 기반의 Pydantic Settings 설정
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """애플리케이션 전역 설정"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # === Application ===
    app_name: str = Field(default="samsung-ai-portal")
    app_env: Literal["development", "staging", "production"] = Field(default="development")
    debug: bool = Field(default=False)
    secret_key: str = Field(default="change-me-in-production")

    # === Server ===
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    workers: int = Field(default=1)

    # === Database ===
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/ai_portal"
    )
    database_pool_size: int = Field(default=20)
    database_max_overflow: int = Field(default=10)
    database_pool_timeout: int = Field(default=30)

    # === Redis ===
    redis_url: str = Field(default="redis://localhost:6379/0")
    redis_password: str | None = Field(default=None)
    redis_max_connections: int = Field(default=50)

    # === Session & Cookie ===
    session_secret_key: str = Field(default="change-me-session-secret")
    session_cookie_name: str = Field(default="ai_portal_session")
    session_cookie_max_age: int = Field(default=86400)  # 24시간
    session_cookie_secure: bool = Field(default=False)  # Production에서는 True
    session_cookie_httponly: bool = Field(default=True)
    session_cookie_samesite: Literal["lax", "strict", "none"] = Field(default="lax")

    # === Auth Mock (개발용) ===
    auth_mock_enabled: bool = Field(default=False, description="인증 모킹 활성화 (개발용)")
    auth_mock_user_id: str = Field(default="mock-user", description="모킹 사용자 ID")
    auth_mock_user_email: str = Field(default="mock@samsung.com", description="모킹 사용자 이메일")
    auth_mock_user_name: str = Field(default="Mock User", description="모킹 사용자 이름")
    auth_mock_user_roles: list[str] = Field(default=["user"], description="모킹 사용자 역할")

    # === SAML 2.0 ===
    saml_strict: bool = Field(default=True)
    saml_debug: bool = Field(default=False)
    saml_sp_entity_id: str = Field(default="")
    saml_sp_acs_url: str = Field(default="")  # Assertion Consumer Service URL
    saml_sp_sls_url: str = Field(default="")  # Single Logout Service URL
    saml_idp_entity_id: str = Field(default="")
    saml_idp_sso_url: str = Field(default="")
    saml_idp_slo_url: str = Field(default="")
    saml_idp_x509_cert: str = Field(default="")

    # === LLM (vLLM 서빙 - Text) ===
    llm_base_url: str = Field(default="http://localhost:8001/v1")
    llm_api_key: str = Field(default="EMPTY")  # vLLM은 보통 API 키 불필요
    llm_model: str = Field(default="")  # vLLM에서 서빙하는 LLM 모델명
    llm_temperature: float = Field(default=0.7)
    llm_max_tokens: int = Field(default=4096)

    # === VLM (vLLM 서빙 - Vision) ===
    vlm_base_url: str = Field(default="http://localhost:8002/v1")
    vlm_api_key: str = Field(default="EMPTY")
    vlm_model: str = Field(default="")  # vLLM에서 서빙하는 VLM 모델명
    vlm_temperature: float = Field(default=0.7)
    vlm_max_tokens: int = Field(default=4096)

    # === Logging ===
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(default="INFO")
    log_format: Literal["json", "console"] = Field(default="json")
    log_file_path: str | None = Field(default=None)

    # === CORS ===
    cors_origins: list[str] = Field(default=["http://localhost:3000", "http://localhost:5173"])
    cors_allow_credentials: bool = Field(default=True)

    # === Crawler ===
    playwright_headless: bool = Field(default=True)
    crawl4ai_verbose: bool = Field(default=False)

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | list[str]) -> list[str]:
        """CORS origins 문자열을 리스트로 변환"""
        if isinstance(v, str):
            import json

            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [origin.strip() for origin in v.split(",")]
        return v

    @property
    def is_development(self) -> bool:
        """개발 환경 여부"""
        return self.app_env == "development"

    @property
    def is_production(self) -> bool:
        """운영 환경 여부"""
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    """
    설정 인스턴스 반환 (캐싱)

    Returns:
        Settings: 애플리케이션 설정 인스턴스
    """
    return Settings()
