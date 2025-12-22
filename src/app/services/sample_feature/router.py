"""
Sample Feature API 라우터

엔드포인트 정의 예시
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.infrastructure.database import get_async_session
from app.common.auth import get_current_user, CurrentUser
from app.services.sample_feature.schemas import (
    SampleCreateRequest,
    SampleUpdateRequest,
    SampleResponse,
    SampleListResponse,
)
from app.services.sample_feature.service import SampleService

router = APIRouter(prefix="/samples", tags=["Sample Feature"])


@router.get("", response_model=SampleListResponse)
async def list_samples(
    skip: int = 0,
    limit: int = 20,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> SampleListResponse:
    """
    샘플 목록 조회

    - **skip**: 건너뛸 개수 (페이지네이션)
    - **limit**: 조회할 개수
    """
    service = SampleService(session)
    items, total = await service.list_samples(skip=skip, limit=limit)
    return SampleListResponse(items=items, total=total)


@router.post("", response_model=SampleResponse, status_code=status.HTTP_201_CREATED)
async def create_sample(
    request: SampleCreateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> SampleResponse:
    """
    샘플 생성
    """
    service = SampleService(session)
    sample = await service.create_sample(request, user_id=current_user.user_id)
    return sample


@router.get("/{sample_id}", response_model=SampleResponse)
async def get_sample(
    sample_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> SampleResponse:
    """
    샘플 상세 조회
    """
    service = SampleService(session)
    sample = await service.get_sample(sample_id)
    return sample


@router.put("/{sample_id}", response_model=SampleResponse)
async def update_sample(
    sample_id: int,
    request: SampleUpdateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> SampleResponse:
    """
    샘플 수정
    """
    service = SampleService(session)
    sample = await service.update_sample(sample_id, request)
    return sample


@router.delete("/{sample_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sample(
    sample_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> None:
    """
    샘플 삭제
    """
    service = SampleService(session)
    await service.delete_sample(sample_id)
