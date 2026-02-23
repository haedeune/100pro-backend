"""
파라미터 관리 서비스 인터페이스 [PRO-B-16].
"""
from typing import Optional, Protocol

from app.infrastructure.task_params.models import SystemParameter
from app.infrastructure.task_params.schemas import ParameterUpdateRequest


class ParameterService(Protocol):
    """시스템 파라미터 CRUD 서비스 인터페이스 [PRO-B-16]."""

    def get_all(self) -> list[SystemParameter]:
        """모든 파라미터를 반환한다."""
        ...

    def get_by_key(self, key: str) -> Optional[SystemParameter]:
        """키로 파라미터를 조회한다."""
        ...

    def get_by_category(self, category: str) -> list[SystemParameter]:
        """카테고리별 파라미터를 조회한다."""
        ...

    def update(self, key: str, request: ParameterUpdateRequest) -> SystemParameter:
        """파라미터 값을 업데이트한다."""
        ...
