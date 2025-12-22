"""
애플리케이션 상수 정의
"""

from enum import Enum


class Environment(str, Enum):
    """환경 구분"""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class ServiceName(str, Enum):
    """서비스 이름 (6개 하위 서비스)"""

    PROMOTION = "promotion"  # 업계프로모션/MI 자동화
    CONTENT_MONITORING = "content_monitoring"  # 컨텐츠 모니터링 (블로그)
    DEEP_SEARCH = "deep_search"  # AI 딥서치 (주식뉴스관련)
    BALANCE_CERTIFICATE = "balance_certificate"  # 잔고증명서 자동발송
    VARIABLE_ANNUITY = "variable_annuity"  # 변액일임 설정/해지 자동화
    OVERSEAS_SETTLEMENT = "overseas_settlement"  # 해외체결내역 자동대사


class UserRole(str, Enum):
    """사용자 역할"""

    ADMIN = "admin"
    MANAGER = "manager"
    USER = "user"
    GUEST = "guest"


class TaskStatus(str, Enum):
    """작업 상태"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# === API 관련 상수 ===
API_V1_PREFIX = "/api/v1"

# === 페이지네이션 ===
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# === 캐시 TTL (초) ===
CACHE_TTL_SHORT = 60  # 1분
CACHE_TTL_MEDIUM = 300  # 5분
CACHE_TTL_LONG = 3600  # 1시간
CACHE_TTL_DAY = 86400  # 24시간

# === 재시도 설정 ===
DEFAULT_RETRY_ATTEMPTS = 3
DEFAULT_RETRY_DELAY = 1.0  # 초

# === LLM 관련 ===
LLM_DEFAULT_TEMPERATURE = 0.7
LLM_MAX_RETRIES = 3

