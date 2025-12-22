"""
Sample 서비스

비즈니스 로직 예시
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.services.sample_feature.models import Sample
from app.services.sample_feature.schemas import (
    SampleCreateRequest,
    SampleUpdateRequest,
    SampleResponse,
)
from app.common.exceptions import NotFoundError
from app.common.logging import get_logger

logger = get_logger(__name__)


class SampleService:
    """
    샘플 서비스

    비즈니스 로직을 처리하는 계층
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_samples(
        self,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[SampleResponse], int]:
        """샘플 목록 조회"""
        # 전체 개수 조회
        count_query = select(func.count()).select_from(Sample)
        count_result = await self._session.execute(count_query)
        total = count_result.scalar() or 0

        # 목록 조회
        query = (
            select(Sample)
            .offset(skip)
            .limit(limit)
            .order_by(Sample.created_at.desc())
        )
        result = await self._session.execute(query)
        samples = result.scalars().all()

        items = [SampleResponse.model_validate(s) for s in samples]
        return items, total

    async def get_sample(self, sample_id: int) -> SampleResponse:
        """샘플 상세 조회"""
        query = select(Sample).where(Sample.id == sample_id)
        result = await self._session.execute(query)
        sample = result.scalar_one_or_none()

        if not sample:
            raise NotFoundError(f"Sample {sample_id} not found")

        return SampleResponse.model_validate(sample)

    async def create_sample(
        self,
        request: SampleCreateRequest,
        user_id: str,
    ) -> SampleResponse:
        """샘플 생성"""
        sample = Sample(
            title=request.title,
            description=request.description,
            created_by=user_id,
        )

        self._session.add(sample)
        await self._session.commit()
        await self._session.refresh(sample)

        logger.info("Sample created", sample_id=sample.id, user_id=user_id)
        return SampleResponse.model_validate(sample)

    async def update_sample(
        self,
        sample_id: int,
        request: SampleUpdateRequest,
    ) -> SampleResponse:
        """샘플 수정"""
        query = select(Sample).where(Sample.id == sample_id)
        result = await self._session.execute(query)
        sample = result.scalar_one_or_none()

        if not sample:
            raise NotFoundError(f"Sample {sample_id} not found")

        # 변경된 필드만 업데이트
        update_data = request.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(sample, field, value)

        await self._session.commit()
        await self._session.refresh(sample)

        logger.info("Sample updated", sample_id=sample_id)
        return SampleResponse.model_validate(sample)

    async def delete_sample(self, sample_id: int) -> None:
        """샘플 삭제"""
        query = select(Sample).where(Sample.id == sample_id)
        result = await self._session.execute(query)
        sample = result.scalar_one_or_none()

        if not sample:
            raise NotFoundError(f"Sample {sample_id} not found")

        await self._session.delete(sample)
        await self._session.commit()

        logger.info("Sample deleted", sample_id=sample_id)
