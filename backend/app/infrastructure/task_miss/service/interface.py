"""
TaskMiss 서비스 인터페이스 [PRO-B-10].
사용자별 누적 task_miss 카운트 집계 및 캐싱 계약을 정의한다.
"""
from typing import Protocol


class TaskMissService(Protocol):
    """사용자별 task_miss 누적 횟수를 제공하는 서비스 인터페이스."""

    def get_cumulative_miss_count(self, user_id: str) -> tuple[int, bool]:
        """
        사용자의 누적 task_miss 횟수를 반환한다.

        Returns:
            (count, cached) — count: 누적 횟수, cached: Redis 캐시 적중 여부
        """
        ...

    def refresh_cache(self, user_id: str) -> int:
        """DB에서 최신 카운트를 조회하여 Redis 캐시를 갱신하고 카운트를 반환한다."""
        ...
