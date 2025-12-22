# Samsung AI Portal

삼성자산운용 AI 서비스 플랫폼 백엔드

## 개요

5개의 AI 기반 자동화 서비스를 제공하는 통합 포털 백엔드입니다.

| 서비스 | 설명 |
|--------|------|
| `mi_automation` | MI 자동화 (업계프로모션, 컨텐츠 모니터링) |
| `deep_search` | AI 딥서치 (주식뉴스) |
| `balance_certificate` | 잔고증명서 자동발송 |
| `variable_annuity` | 변액일임 설정/해지 자동화 |
| `overseas_settlement` | 해외체결내역 자동대사 |

### MI 자동화 하위 서비스

| 서비스 | 설명 |
|--------|------|
| `mi_automation/promotion` | 업계프로모션 자동화 |
| `mi_automation/contents_monitoring` | 컨텐츠 모니터링 (블로그) |

---

## 🛠 기술 스택

| 분류 | 기술 |
|------|------|
| **Framework** | FastAPI, Python 3.12+ |
| **Package Manager** | uv |
| **Database** | PostgreSQL (asyncpg) |
| **Cache** | Redis (hiredis) |
| **ORM** | SQLAlchemy 2.0 (async) |
| **LLM** | LangChain, LangGraph (vLLM 서빙) |
| **Crawling** | Playwright, Crawl4AI |
| **Auth** | SAML 2.0 SSO, Cookie Session |
| **Logging** | structlog |

---

## 📁 프로젝트 구조

```
samsung_ai_portal/
├── pyproject.toml          # 의존성 및 프로젝트 설정
├── alembic/                # DB 마이그레이션
│   ├── env.py
│   └── versions/
├── scripts/
│   ├── start.sh            # Unix/Mac 시작 스크립트
│   └── start.bat           # Windows 시작 스크립트
│
└── src/app/
    ├── main.py             # FastAPI 앱 진입점
    │
    ├── config/             # 설정
    │   ├── settings.py     # 환경변수 기반 설정 (Pydantic Settings)
    │   └── constants.py    # 상수 정의
    |
    ├── llm/                # LLM 관련 코드
    |   ├──agents/          # Agent 모듈
    |   └──core/            # 공통 모듈
    |   └──prompts/         # 프롬프트 
    │
    ├── common/             # 공통 모듈
    │   ├── auth/           # 인증 (SAML, Cookie, Session)
    │   ├── infrastructure/ # DB, Redis 연결
    │   ├── logging/        # structlog 기반 로깅
    │   ├── middleware/     # CORS, 요청 컨텍스트
    │   ├── exceptions/     # 전역 예외 처리
    │   └── utils/          # 비동기 유틸리티
    │
    ├── api/
    │   └── v1/
    │       ├── router.py   # 모든 서비스 라우터 통합
    │       └── deps.py     # 공통 의존성 타입
    │
    └── services/           # 서비스별 모듈
        ├── sample_feature/ # 구조 가이드라인 (참고용)
        │   ├── __init__.py
        │   ├── router.py   # 엔드포인트
        │   ├── models.py   # DB 모델
        │   ├── schemas.py  # 요청/응답 스키마
        │   └── service.py  # 비즈니스 로직
        ├── mi_automation/          # MI 자동화
        │   ├── promotion/          # 업계프로모션
        │   └── contents_monitoring/ # 컨텐츠 모니터링
        ├── deep_search/
        ├── balance_certificate/
        ├── variable_annuity/
        └── overseas_settlement/
```

---

## 🚀 시작하기

### 1. 환경 설정

```bash
# 의존성 설치
uv sync

# 환경변수 설정
cp .env.example .env
# .env 파일 수정
```

### 2. 인프라 실행 (PostgreSQL, Redis)

```bash
# 로컬에 PostgreSQL, Redis 설치 필요
# 또는 별도 서버 사용
```

### 3. 서버 실행

```bash
# Mac/Linux
./scripts/start.sh

# Windows
scripts\start.bat

# 또는 직접 실행
PYTHONPATH=src uvicorn app.main:app --reload
```

### 4. API 문서 확인

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## 📝 개발 가이드라인

### 서비스 구조

각 서비스는 다음 파일로 구성됩니다:

```
service_name/
├── __init__.py     # 모듈 초기화, router export
├── router.py       # FastAPI 엔드포인트
├── models.py       # SQLAlchemy 모델
├── schemas.py      # Pydantic 스키마
└── service.py      # 비즈니스 로직
```

### 파일이 커지면 폴더로 전환

```
service.py  →  service/
               ├── __init__.py    # re-export
               ├── crud.py
               └── llm.py
```

### 흐름

```
Router → Service → Model
         ↓
      Schema (요청/응답 변환)
```

### 새 서비스 추가 방법

1. `services/` 폴더에 새 서비스 폴더 생성
2. `sample_feature/` 구조 참고하여 파일 작성
3. `api/v1/router.py`에 라우터 등록
4. `alembic/env.py`에 모델 import 추가

---

## 🔐 인증

### SAML 2.0 SSO

- IdP(Identity Provider)를 통한 SSO 인증
- `.env`에서 SAML 설정 필요

### Cookie Session

- Redis 기반 세션 저장
- 로컬/도메인 환경 모두 지원

---

## 🤖 LLM 설정

vLLM으로 서빙되는 모델을 LangChain OpenAI 호환 API로 연결합니다.

```python
from langchain_openai import ChatOpenAI
from app.config import get_settings

settings = get_settings()

# LLM (Text)
llm = ChatOpenAI(
    base_url=settings.llm_base_url,
    api_key=settings.llm_api_key,
    model=settings.llm_model,
)

# VLM (Vision)
vlm = ChatOpenAI(
    base_url=settings.vlm_base_url,
    api_key=settings.vlm_api_key,
    model=settings.vlm_model,
)
```

---

## 📦 주요 패키지

### Core
- `fastapi` - 웹 프레임워크
- `uvicorn` - ASGI 서버
- `pydantic` - 데이터 검증
- `pydantic-settings` - 환경변수 설정

### Database
- `sqlalchemy[asyncio]` - 비동기 ORM
- `asyncpg` - PostgreSQL 비동기 드라이버
- `alembic` - DB 마이그레이션

### Cache
- `redis[hiredis]` - Redis 비동기 클라이언트

### LLM
- `langchain` - LLM 프레임워크
- `langchain-openai` - OpenAI/vLLM 연결
- `langgraph` - LLM 워크플로우

### Crawling
- `playwright` - 브라우저 자동화
- `crawl4ai` - AI 친화적 크롤링

### Auth
- `python3-saml` - SAML 2.0
- `itsdangerous` - 쿠키 서명

### Logging
- `structlog` - 구조화된 로깅

### Utilities
- `httpx` - 비동기 HTTP 클라이언트
- `orjson` - 빠른 JSON 직렬화
- `tenacity` - 재시도 로직

---

## ⚠️ 주의사항

### 비동기 처리

모든 I/O 작업은 비동기로 처리해야 합니다. 동기 함수가 이벤트 루프를 블로킹하지 않도록 주의하세요.

```python
# ❌ 동기 함수 직접 호출 (블로킹)
result = blocking_function()

# ✅ 스레드 풀에서 실행
from app.common.utils import run_in_executor
result = await run_in_executor(blocking_function)
```

### DB 세션

세션은 자동 커밋되지 않습니다. 명시적으로 `commit()`을 호출하세요.

```python
self._session.add(entity)
await self._session.commit()
await self._session.refresh(entity)
```

---