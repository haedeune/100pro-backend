"""
전략 선택 API 라우터 [PRO-B-21].
과업 상태 전환(Archive/Modify/Keep), 실험 분기 조회, 활성 과업 목록 엔드포인트를 제공한다.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Path

from app.domains.task.schemas import TaskResponse
from app.infrastructure.task_miss.service import TaskMissServiceImpl
from app.infrastructure.task_strategy.experiment import ExperimentAssigner
from app.infrastructure.task_strategy.schemas import (
    ActiveTaskListResponse,
    ApplyStrategyRequest,
    ApplyStrategyResponse,
    ExperimentAssignmentResponse,
)
from app.infrastructure.task_strategy.service import TaskStrategyServiceImpl

router = APIRouter()

_strategy_service: TaskStrategyServiceImpl | None = None
_miss_service: TaskMissServiceImpl | None = None


def _get_strategy_service() -> TaskStrategyServiceImpl:
    global _strategy_service
    if _strategy_service is None:
        _strategy_service = TaskStrategyServiceImpl()
    return _strategy_service


def _get_miss_service() -> TaskMissServiceImpl:
    global _miss_service
    if _miss_service is None:
        _miss_service = TaskMissServiceImpl()
    return _miss_service


# ── 1. 전략 적용 ──────────────────────────────────────────────

@router.post(
    "/tasks/{task_id}/apply-strategy",
    response_model=ApplyStrategyResponse,
    summary="[PRO-B-21] 과업에 전략(Archive/Modify/Keep) 적용",
)
def apply_strategy(
    task_id: int = Path(..., description="과업 ID"),
    body: ApplyStrategyRequest = ...,
) -> ApplyStrategyResponse:
    """
    strategy_select 값에 매핑되는 상태 코드로 DB 레코드를 업데이트한다.
    Archive 선택 시 해당 과업을 활성 리스트 쿼리에서 제외한다.
    """
    service = _get_strategy_service()
    try:
        return service.apply_strategy(task_id, body)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ── 2. 실험 분기 조회 ─────────────────────────────────────────

@router.get(
    "/users/{user_id}/experiment",
    response_model=ExperimentAssignmentResponse,
    summary="[PRO-B-21] 사용자 실험군/대조군 할당 조회",
)
def get_experiment_assignment(
    user_id: str = Path(..., description="사용자 식별자"),
) -> ExperimentAssignmentResponse:
    """
    누적 miss_count와 TRIGGER_MISS_THRESHOLD를 비교하여 실험 자격을 판정하고,
    자격 충족 시 SHA-256 해시 기반으로 실험군/대조군을 할당한다.
    """
    miss_service = _get_miss_service()
    count, _ = miss_service.get_cumulative_miss_count(user_id)

    result = ExperimentAssigner.assign(user_id, count)

    return ExperimentAssignmentResponse(
        user_id=result.user_id,
        cumulative_miss_count=result.cumulative_miss_count,
        trigger_threshold=result.trigger_threshold,
        eligible=result.eligible,
        feature_flag_enabled=result.feature_flag_enabled,
        group=result.group,
        timestamp=datetime.now(timezone.utc),
    )


# ── 3. 활성 과업 목록 (보관 제외) ────────────────────────────

@router.get(
    "/users/{user_id}/active-tasks",
    response_model=ActiveTaskListResponse,
    summary="[PRO-B-21] 활성 과업 목록 조회 (보관 과업 제외)",
)
def get_active_tasks(
    user_id: str = Path(..., description="사용자 식별자"),
) -> ActiveTaskListResponse:
    """is_archived=False인 과업만 반환한다. Archive 전략이 적용된 과업은 제외된다."""
    service = _get_strategy_service()
    tasks = service.get_active_tasks(user_id)
    task_dtos = [TaskResponse.model_validate(t) for t in tasks]
    return ActiveTaskListResponse(
        user_id=user_id,
        total_count=len(task_dtos),
        tasks=task_dtos,
        timestamp=datetime.now(timezone.utc),
    )
