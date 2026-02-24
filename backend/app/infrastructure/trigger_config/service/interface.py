"""
트리거 설정 서비스 인터페이스 [PRO-B-25].
"""
from typing import Protocol


class TriggerConfigService(Protocol):
    """[PRO-B-25] 트리거 임계치·운영 변수 조회 및 제어 서비스."""

    def get_settings(self) -> dict:
        """현재 설정값을 반환한다."""
        ...

    def check_trigger(self, user_id: str) -> dict:
        """사용자의 트리거 충족 여부를 판정한다."""
        ...

    def check_archive_capacity(self, user_id: str) -> dict:
        """보관함 적재 가능 여부를 검증한다."""
        ...

    def update_parameter(self, key: str, value: str) -> dict:
        """파라미터 값을 업데이트한다."""
        ...
