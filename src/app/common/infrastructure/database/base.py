"""
SQLAlchemy Base 모델

모든 엔티티 모델의 기반 클래스

네이밍 컨벤션 (DB 레벨):
- 테이블명: 대문자, 접두사 TB_ (예: TB_SAMPLE)
- 컬럼명: 소문자, 접두사 col_ (예: col_title)
- 자동 증분 ID: col_id
- Unique ID: col_uid

Python 속성명은 기존과 동일하게 사용 (id, title 등)
"""

from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column


class Base(DeclarativeBase):
    """
    SQLAlchemy 선언적 베이스 클래스

    모든 모델은 이 클래스를 상속받아야 함
    테이블명은 TB_ 접두사 + 대문자로 자동 생성됨
    """

    @declared_attr.directive
    def __tablename__(cls) -> str:
        """
        클래스명을 테이블명으로 변환

        규칙: TB_ + SNAKE_CASE (대문자)
        예시: SampleFeature -> TB_SAMPLE_FEATURE
        """
        name = cls.__name__
        # CamelCase -> SNAKE_CASE (대문자)
        result = [name[0].upper()]
        for char in name[1:]:
            if char.isupper():
                result.extend(["_", char])
            else:
                result.append(char.upper())
        return f"TB_{''.join(result)}"


class TimestampMixin:
    """
    타임스탬프 믹스인

    생성일시(col_created_at), 수정일시(col_updated_at) 자동 관리
    Python에서는 created_at, updated_at으로 접근
    """

    created_at: Mapped[datetime] = mapped_column(
        "col_created_at",  # DB 컬럼명
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="작성일",
    )
    updated_at: Mapped[datetime] = mapped_column(
        "col_updated_at",  # DB 컬럼명
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="수정일",
    )


class AuditMixin:
    """
    감사(Audit) 믹스인

    작성자(col_created_by_id), 수정자(col_updated_by_id) 관리
    Python에서는 created_by_id, updated_by_id로 접근
    """

    created_by_id: Mapped[int | None] = mapped_column(
        "col_created_by_id",  # DB 컬럼명
        BigInteger,
        nullable=True,
        comment="작성자 ID",
    )
    updated_by_id: Mapped[int | None] = mapped_column(
        "col_updated_by_id",  # DB 컬럼명
        BigInteger,
        nullable=True,
        comment="수정자 ID",
    )


class SoftDeleteMixin:
    """
    소프트 삭제 믹스인

    실제 삭제 대신 col_deleted_at 플래그 설정
    Python에서는 deleted_at으로 접근
    """

    deleted_at: Mapped[datetime | None] = mapped_column(
        "col_deleted_at",  # DB 컬럼명
        DateTime(timezone=True),
        nullable=True,
        default=None,
        comment="삭제일",
    )

    @property
    def is_deleted(self) -> bool:
        """삭제 여부"""
        return self.deleted_at is not None


class BaseModel(Base, TimestampMixin):
    """
    기본 모델

    포함 컬럼 (DB명 -> Python명):
    - col_id -> id: 자동 증분 PK
    - col_created_at -> created_at: 작성일
    - col_updated_at -> updated_at: 수정일
    """

    __abstract__ = True

    id: Mapped[int] = mapped_column(
        "col_id",  # DB 컬럼명
        primary_key=True,
        autoincrement=True,
        comment="자동 증분 ID",
    )

    def to_dict(self) -> dict[str, Any]:
        """모델을 딕셔너리로 변환 (Python 속성명 사용)"""
        return {c.key: getattr(self, c.key) for c in self.__table__.columns}


class AuditableModel(Base, TimestampMixin, AuditMixin):
    """
    감사 가능 모델

    포함 컬럼 (DB명 -> Python명):
    - col_id -> id: 자동 증분 PK
    - col_created_at -> created_at: 작성일
    - col_updated_at -> updated_at: 수정일
    - col_created_by_id -> created_by_id: 작성자 ID
    - col_updated_by_id -> updated_by_id: 수정자 ID
    """

    __abstract__ = True

    id: Mapped[int] = mapped_column(
        "col_id",  # DB 컬럼명
        primary_key=True,
        autoincrement=True,
        comment="자동 증분 ID",
    )

    def to_dict(self) -> dict[str, Any]:
        """모델을 딕셔너리로 변환 (Python 속성명 사용)"""
        return {c.key: getattr(self, c.key) for c in self.__table__.columns}
