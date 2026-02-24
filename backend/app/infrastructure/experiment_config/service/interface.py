"""
실험 설정 서비스 인터페이스 [PRO-B-22].
"""
from typing import Protocol

from app.infrastructure.experiment_config.validators import ValidationResult


class ExperimentConfigService(Protocol):
    """실험 설정 조회 및 운영 검증 서비스 인터페이스 [PRO-B-22]."""

    def get_current_config(self) -> dict:
        """현재 실험·운영 설정값을 반환한다."""
        ...

    def check_trigger(self, user_id: str) -> dict:
        """사용자의 트리거 임계치 충족 여부와 전략 옵션을 반환한다."""
        ...

    def check_archive_limit(self, user_id: str) -> ValidationResult:
        """보관함 상한 검증."""
        ...
