"""
상태 전환 서비스 인터페이스 [PRO-B-23].
전략 선택에 따른 상태 전환, 보관함 조회, 변경 이력 조회 계약을 정의한다.
"""
from typing import Protocol

from app.infrastructure.task_archive.models import TaskArchive, TaskStatusHistory
from app.infrastructure.task_archive.schemas import TransitionRequest, TransitionResponse


class TaskArchiveService(Protocol):
    """전략 기반 상태 전환 및 보관함 관리 서비스 인터페이스."""

    def apply_transition(self, task_id: int, request: TransitionRequest) -> TransitionResponse:
        """전략에 따라 과업 상태를 전환하고, Archive 시 보관함으로 격리한다."""
        ...

    def get_user_archives(self, user_id: str) -> list[TaskArchive]:
        """사용자의 보관함 과업 목록을 반환한다."""
        ...

    def get_task_history(self, task_id: int) -> list[TaskStatusHistory]:
        """특정 과업의 상태 변경 이력을 반환한다."""
        ...
