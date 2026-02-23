"""
task_miss 인프라 API 라우터 [PRO-B-10].
사용자별 누적 miss count 조회 및 배치 수동 실행 엔드포인트를 제공한다.
"""
import time
from datetime import datetime, timezone

from fastapi import APIRouter, Path

from app.domains.task.schemas import CumulativeMissCountResponse, TaskMissBatchResultResponse
from app.infrastructure.task_miss.scheduler import TaskMissScheduler
from app.infrastructure.task_miss.service import TaskMissServiceImpl

router = APIRouter()

_service: TaskMissServiceImpl | None = None


def _get_service() -> TaskMissServiceImpl:
    global _service
    if _service is None:
        _service = TaskMissServiceImpl()
    return _service


@router.get(
    "/users/{user_id}/miss-count",
    response_model=CumulativeMissCountResponse,
    summary="사용자별 누적 task_miss 카운트 조회",
)
def get_cumulative_miss_count(
    user_id: str = Path(..., description="사용자 식별자"),
) -> CumulativeMissCountResponse:
    """사용자의 전체 기간 누적 task_miss 횟수를 Redis 캐시 우선으로 반환한다."""
    service = _get_service()
    count, cached = service.get_cumulative_miss_count(user_id)
    return CumulativeMissCountResponse(
        user_id=user_id,
        cumulative_miss_count=count,
        cached=cached,
        timestamp=datetime.now(timezone.utc),
    )


@router.post(
    "/users/{user_id}/miss-count/refresh",
    response_model=CumulativeMissCountResponse,
    summary="사용자별 miss count 캐시 강제 갱신",
)
def refresh_miss_count_cache(
    user_id: str = Path(..., description="사용자 식별자"),
) -> CumulativeMissCountResponse:
    """DB에서 최신 카운트를 재집계하고 Redis 캐시를 갱신한다."""
    service = _get_service()
    count = service.refresh_cache(user_id)
    return CumulativeMissCountResponse(
        user_id=user_id,
        cumulative_miss_count=count,
        cached=False,
        timestamp=datetime.now(timezone.utc),
    )


@router.post(
    "/batch/run",
    response_model=TaskMissBatchResultResponse,
    summary="task_miss 상태 전환 배치 수동 실행",
)
def run_batch_now() -> TaskMissBatchResultResponse:
    """기한 만료 과업을 즉시 task_miss로 전환하는 배치를 1회 실행한다."""
    start_ns = time.perf_counter_ns()
    transitioned = TaskMissScheduler.run_now()
    elapsed_ms = (time.perf_counter_ns() - start_ns) / 1_000_000
    return TaskMissBatchResultResponse(
        transitioned_count=transitioned,
        execution_time_ms=round(elapsed_ms, 3),
        timestamp=datetime.now(timezone.utc),
    )
