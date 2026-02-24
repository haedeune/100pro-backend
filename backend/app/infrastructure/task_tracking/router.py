"""
행동 트래킹 및 실험 분기 API 라우터 [PRO-B-24].
이벤트 기록, 행동 체인 조회, 실험 할당, 그룹별 API 응답 분기 엔드포인트를 제공한다.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Path

from app.core.database import get_session_factory
from app.infrastructure.task_tracking.experiment import PersistentExperimentAssigner
from app.infrastructure.task_tracking.schemas import (
    BehaviorChainResponse,
    BehaviorLogResponse,
    BranchedResponse,
    ExperimentInfoResponse,
    RecordEventRequest,
    UserBehaviorSummaryResponse,
)
from app.infrastructure.task_tracking.service import BehaviorTrackingServiceImpl

router = APIRouter()

_service: BehaviorTrackingServiceImpl | None = None


def _get_service() -> BehaviorTrackingServiceImpl:
    global _service
    if _service is None:
        _service = BehaviorTrackingServiceImpl()
    return _service


# ── 1. 행동 이벤트 기록 ──────────────────────────────────────

@router.post(
    "/events",
    response_model=BehaviorLogResponse,
    summary="[PRO-B-24] 행동 이벤트 기록 (experiment_id 자동 결합)",
)
def record_event(body: RecordEventRequest) -> BehaviorLogResponse:
    """
    과업 이벤트를 기록한다. 직전 이벤트와의 latency(ms)를 자동 계산하고,
    사용자의 Experiment ID를 결합하여 저장한다.
    """
    service = _get_service()
    log = service.record_event(body)
    return BehaviorLogResponse.model_validate(log)


# ── 2. 행동 체인 조회 ────────────────────────────────────────

@router.get(
    "/tasks/{task_id}/chain",
    response_model=BehaviorChainResponse,
    summary="[PRO-B-24] task_id 기준 행동 체인 조회",
)
def get_behavior_chain(
    task_id: int = Path(..., description="과업 ID"),
) -> BehaviorChainResponse:
    """task_id를 기준으로 실패→보관→성공 과정의 이벤트 체인을 시간순으로 반환한다."""
    service = _get_service()
    logs = service.get_behavior_chain(task_id)
    items = [BehaviorLogResponse.model_validate(log) for log in logs]

    total_latency = None
    if len(logs) >= 2:
        first_at = logs[0].event_at
        last_at = logs[-1].event_at
        total_latency = round((last_at - first_at).total_seconds() * 1000, 3)

    return BehaviorChainResponse(
        task_id=task_id,
        total_events=len(items),
        chain=items,
        total_latency_ms=total_latency,
        timestamp=datetime.now(timezone.utc),
    )


# ── 3. 실험 할당 조회/생성 ───────────────────────────────────

@router.get(
    "/users/{user_id}/experiment",
    response_model=ExperimentInfoResponse,
    summary="[PRO-B-24] 사용자 실험군 할당 조회 (없으면 신규 할당)",
)
def get_experiment_assignment(
    user_id: str = Path(..., description="사용자 식별자"),
) -> ExperimentInfoResponse:
    """사용자의 실험군 할당 정보를 반환한다. 미할당 시 해시 기반으로 신규 할당한다."""
    session_factory = get_session_factory()
    with session_factory() as session:
        result = PersistentExperimentAssigner.get_or_assign(session, user_id)
        session.commit()
    return ExperimentInfoResponse(
        user_id=result.user_id,
        experiment_id=result.experiment_id,
        group=result.group,
        hash_value=result.hash_value,
        assigned_at=result.assigned_at,
        newly_assigned=result.newly_assigned,
    )


# ── 4. 실험군별 API 응답 분기 (Response Branching) ───────────

@router.get(
    "/users/{user_id}/branched-response",
    response_model=BranchedResponse,
    summary="[PRO-B-24] 실험군/대조군 분기 응답",
)
def get_branched_response(
    user_id: str = Path(..., description="사용자 식별자"),
) -> BranchedResponse:
    """
    실험군(treatment)과 대조군(control)에 서로 다른 응답 payload를 반환한다.
    Feature Flag에 따른 Response Branching 처리의 참조 구현.
    """
    session_factory = get_session_factory()
    with session_factory() as session:
        result = PersistentExperimentAssigner.get_or_assign(session, user_id)
        session.commit()

    # [PRO-B-24] 그룹별 응답 분기
    if result.group == "treatment":
        variant = "treatment_v1"
        payload = {
            "show_strategy_prompt": True,
            "prompt_style": "detailed",
            "retry_suggestion": True,
            "message": "과업을 재설정하거나 보관할 수 있습니다.",
        }
    else:
        variant = "control_default"
        payload = {
            "show_strategy_prompt": False,
            "prompt_style": "minimal",
            "retry_suggestion": False,
            "message": "미완료 과업이 있습니다.",
        }

    return BranchedResponse(
        user_id=result.user_id,
        experiment_id=result.experiment_id,
        group=result.group,
        response_variant=variant,
        payload=payload,
        timestamp=datetime.now(timezone.utc),
    )


# ── 5. 사용자 행동 요약 ──────────────────────────────────────

@router.get(
    "/users/{user_id}/summary",
    response_model=UserBehaviorSummaryResponse,
    summary="[PRO-B-24] 사용자 행동 요약 통계",
)
def get_user_summary(
    user_id: str = Path(..., description="사용자 식별자"),
) -> UserBehaviorSummaryResponse:
    """사용자별 이벤트 유형 카운트, 평균 latency, 실험 정보를 요약 반환한다."""
    service = _get_service()
    summary = service.get_user_summary(user_id)
    return UserBehaviorSummaryResponse(
        user_id=user_id,
        experiment_id=summary["experiment_id"],
        experiment_group=summary["experiment_group"],
        total_events=summary["total_events"],
        event_type_counts=summary["event_type_counts"],
        avg_latency_ms=summary["avg_latency_ms"],
        timestamp=datetime.now(timezone.utc),
    )
