"""
Sample SQLAlchemy 모델

DB 테이블 정의 예시

네이밍 컨벤션 (DB 레벨):
- 테이블명: TB_ 접두사 + 대문자 (예: TB_SAMPLE)
- 컬럼명: col_ 접두사 + 소문자 (예: col_title)

Python 속성명은 기존과 동일하게 사용
"""

from sqlalchemy import String, Text, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.common.infrastructure.database.base import BaseModel
from app.config.constants import TaskStatus


class Sample(BaseModel):
    """
    샘플 엔티티

    BaseModel을 상속받으면 자동으로:
    - col_id -> id (PK, auto increment)
    - col_created_at -> created_at (작성일)
    - col_updated_at -> updated_at (수정일)
    - __tablename__ (TB_ + 클래스명 대문자 → TB_SAMPLE)
    """

    # 테이블명 명시적 지정 (자동 생성과 동일: TB_SAMPLE)
    __tablename__ = "TB_SAMPLE"

    title: Mapped[str] = mapped_column(
        "col_title",  # DB 컬럼명
        String(255),
        nullable=False,
        comment="제목",
    )
    description: Mapped[str | None] = mapped_column(
        "col_description",  # DB 컬럼명
        Text,
        nullable=True,
        comment="설명",
    )
    status: Mapped[TaskStatus] = mapped_column(
        "col_status",  # DB 컬럼명
        SQLEnum(TaskStatus),
        default=TaskStatus.PENDING,
        nullable=False,
        comment="상태",
    )
    created_by: Mapped[str | None] = mapped_column(
        "col_created_by",  # DB 컬럼명
        String(100),
        nullable=True,
        comment="생성자 ID",
    )
