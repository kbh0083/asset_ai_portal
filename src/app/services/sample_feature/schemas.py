"""
Sample Pydantic 스키마

API 요청/응답 스키마 정의 예시
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.config.constants import TaskStatus


# === 요청 스키마 ===

class SampleCreateRequest(BaseModel):
    """샘플 생성 요청"""

    title: str = Field(..., min_length=1, max_length=255, description="제목")
    description: str | None = Field(None, description="설명")


class SampleUpdateRequest(BaseModel):
    """샘플 수정 요청"""

    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    status: TaskStatus | None = None


# === 응답 스키마 ===

class SampleResponse(BaseModel):
    """샘플 응답"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    status: TaskStatus
    created_by: str | None
    created_at: datetime
    updated_at: datetime


class SampleListResponse(BaseModel):
    """샘플 목록 응답"""

    items: list[SampleResponse]
    total: int
