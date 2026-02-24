"""
전략 서비스 인터페이스 [PRO-B-21].
Archive / Modify / Keep 전략 적용 및 활성 과업 조회 계약을 정의한다.
"""
from typing import Protocol

from app.domains.task.models import Task
from app.infrastructure.task_strategy.schemas import ApplyStrategyRequest, ApplyStrategyResponse


class TaskStrategyService(Protocol):
    """전략 선택에 따른 과업 상태 전환 서비스 인터페이스."""

    def apply_strategy(self, task_id: int, request: ApplyStrategyRequest) -> ApplyStrategyResponse:
        """과업에 전략을 적용하고 결과를 반환한다."""
        ...

    def get_active_tasks(self, user_id: str) -> list[Task]:
        """보관(archive)되지 않은 활성 과업 목록을 반환한다."""
        ...
