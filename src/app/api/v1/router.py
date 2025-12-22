"""
API v1 라우터 통합

모든 서비스 라우터를 여기서 통합
"""

from fastapi import APIRouter

# Sample Feature (구조 가이드라인용 - 운영 시 제거)
from app.services.sample_feature import router as sample_router

api_router = APIRouter()

# === Sample Feature (운영 시 제거) ===
api_router.include_router(sample_router)


# === 실제 서비스 라우터 등록 ===
# 각 서비스 구현 후 아래 주석을 해제하세요

# from app.services.promotion.router import router as promotion_router
# api_router.include_router(promotion_router)

# from app.services.content_monitoring.router import router as content_monitoring_router
# api_router.include_router(content_monitoring_router)

# from app.services.deep_search.router import router as deep_search_router
# api_router.include_router(deep_search_router)

# from app.services.balance_certificate.router import router as balance_certificate_router
# api_router.include_router(balance_certificate_router)

# from app.services.variable_annuity.router import router as variable_annuity_router
# api_router.include_router(variable_annuity_router)

# from app.services.overseas_settlement.router import router as overseas_settlement_router
# api_router.include_router(overseas_settlement_router)
