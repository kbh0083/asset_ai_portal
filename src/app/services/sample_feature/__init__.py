"""
Sample Feature - 구조 가이드라인

이 모듈은 새로운 서비스를 만들 때 참고할 수 있는 샘플입니다.
실제 운영 시에는 이 폴더를 삭제하세요.

## 서비스 구조 (기본)

```
service_name/
├── __init__.py     # 서비스 모듈 초기화
├── router.py       # FastAPI 라우터 (엔드포인트)
├── models.py       # SQLAlchemy 모델 (DB 테이블)
├── schemas.py      # Pydantic 스키마 (요청/응답)
└── service.py      # 비즈니스 로직
```

## 파일이 커지면 폴더로 전환

파일이 너무 커지면 폴더로 변환하고 기능별로 분리합니다.
__init__.py에서 re-export하면 기존 import가 깨지지 않습니다.

### service.py → service/ 폴더 전환 예시

```
service.py  →  service/
               ├── __init__.py    # re-export
               ├── crud.py        # CRUD 로직
               ├── llm.py         # LLM 관련
               └── crawler.py     # 크롤링 관련
```

service/__init__.py 작성 예시:
```python
from app.services.xxx.service.crud import XXXCRUDService
from app.services.xxx.service.llm import XXXLLMService

__all__ = ["XXXCRUDService", "XXXLLMService"]
```

### models.py, schemas.py도 동일하게 적용 가능

```
models.py  →  models/
              ├── __init__.py
              ├── user.py
              └── item.py
```

## 흐름
Router → Service → Model
         ↓
      Schema (요청/응답 변환)
"""

from app.services.sample_feature.router import router

__all__ = ["router"]
