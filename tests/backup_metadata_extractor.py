"""
해외체결대사 Metadata Extractor 태스크

역할:
    - Document Parser 이후 단계
    - 추출된 텍스트를 기반으로 LLM/룰을 사용해 거래 데이터를 추출
    - OverseaConfirmationData 테이블에 저장
"""

from __future__ import annotations

from datetime import datetime

from app.common.infrastructure.cache.redis import get_redis_client_instance
from app.common.logging import get_logger
from app.common.task_queue.schemas import TaskContext, TaskPayload, TaskType

logger = get_logger(__name__)


class OSMetadataExtractor:
    """해외체결대사 Metadata Extractor"""

    TASK_QUEUE_KEY = "task_queue:pending"
    NEXT_HANDLER_PATH = "app.services.overseas_settlement.tasks.interface_sender.run"

    @classmethod
    async def run(cls, context: TaskContext) -> dict:
        task_id: int | None = context.config.get("task_id")
        parent_task_id: str | None = context.config.get("parent_task_id")

        if not task_id:
            raise ValueError("task_id 가 필요합니다")

        logger.info(
            "OS Metadata Extractor 태스크 시작",
            task_id=context.task_id,
            os_task_id=task_id,
        )

        # TODO: LLM 기반 해외거래체결내역 데이터 추출 및 DB 저장
        #   1. Document Parser에서 추출한 텍스트 로드
        #   2. LLM 또는 룰 기반으로 다음 필드 추출:
        #      - trade_date: 거래일
        #      - fund_name: 펀드 명
        #      - fund_code: 펀드 코드
        #      - ticker: 종목 티커
        #      - isin: 국제증권식별번호
        #      - security_name: 종목명
        #      - settlement_date: 결제일
        #      - buy_sell: 매수/매도 (B / S)
        #      - currency_code: 통화 코드
        #      - executed_qty: 체결 수량
        #      - deal_price: 체결 단가
        #      - gross_amount: 총 금액
        #      - commission: 수수료
        #      - taxes: 세금
        #      - other_charges: 기타 비용
        #      - net_settlement_amt: 순 정산금액
        #      - executing_broker: 거래 실행 브로커
        #      - clearing_broker: 거래 청산 브로커
        #      - settlement_location_pset: 결제장소
        #      - sec_account: 증권 계좌
        #      - clearing_agent_id: 청산/결제 기관 식별 코드
        #   3. OverseaConfirmationData 테이블에 저장

        queued = await cls._enqueue_interface_sender_task(
            task_id=task_id,
            parent_task_id=parent_task_id or context.task_id,
        )

        logger.info(
            "OS Metadata Extractor 태스크 완료",
            task_id=context.task_id,
            os_task_id=task_id,
            next_queued=queued,
        )

        return {
            "status": "completed",
            "task_id": task_id,
            "next_queued": queued,
        }

    @classmethod
    async def _enqueue_interface_sender_task(
        cls,
        task_id: int,
        parent_task_id: str,
    ) -> bool:
        """Interface Sender 태스크를 큐에 등록"""
        redis = await get_redis_client_instance()

        payload = TaskPayload(
            execution_id=f"{parent_task_id}-iface-{task_id}",
            definition_id="send_overseas_interface",
            service_code="overseas_settlement",
            task_name=f"interface_sender_{task_id}",
            task_type=TaskType.SYNC,
            handler_path=cls.NEXT_HANDLER_PATH,
            config={
                "task_id": task_id,
                "parent_task_id": parent_task_id,
            },
            timeout_seconds=300,
            max_retry=2,
            retry_count=0,
            scheduled_at=datetime.now(),
        )

        await redis.rpush(cls.TASK_QUEUE_KEY, payload.model_dump_json())

        logger.debug(
            "Interface Sender 태스크 큐에 등록",
            task_id=task_id,
            execution_id=payload.execution_id,
        )

        return True


run = OSMetadataExtractor.run
