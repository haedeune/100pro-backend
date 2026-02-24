"""
행동 트래킹 서비스 인터페이스 [PRO-B-24].
이벤트 기록, 행동 체인 조회, 사용자 요약 계약을 정의한다.
"""
from typing import Protocol

from app.infrastructure.task_tracking.models import BehaviorLog
from app.infrastructure.task_tracking.schemas import RecordEventRequest


class BehaviorTrackingService(Protocol):
    """행동 체인 트래킹 서비스 인터페이스 [PRO-B-24]."""

    def record_event(self, request: RecordEventRequest) -> BehaviorLog:
        """이벤트를 기록하고 experiment_id를 자동 결합한다."""
        ...

    def get_behavior_chain(self, task_id: int) -> list[BehaviorLog]:
        """task_id 기준 행동 체인을 시간순으로 반환한다."""
        ...

    def get_user_summary(self, user_id: str) -> dict:
        """사용자별 행동 요약 통계를 반환한다."""
        ...
