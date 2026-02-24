"""
보관함 및 상태 전환 API 라우터 [PRO-B-23].
전략 적용(Archive/Modify/Keep), 보관함 목록 조회, 상태 변경 이력 조회 엔드포인트를 제공한다.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Path

from app.infrastructure.task_archive.schemas import (
    ArchiveItemResponse,
    ArchiveListResponse,
    StatusHistoryItemResponse,
    StatusHistoryListResponse,
    TransitionRequest,
    TransitionResponse,
)
from app.infrastructure.task_archive.service import TaskArchiveServiceImpl

router = APIRouter()

_service: TaskArchiveServiceImpl | None = None


def _get_service() -> TaskArchiveServiceImpl:
    global _service
    if _service is None:
        _service = TaskArchiveServiceImpl()
    return _service


# ── 1. 전략 적용 (상태 전환 + 보관함 격리) ─────────────────────

@router.post(
    "/tasks/{task_id}/transition",
    response_model=TransitionResponse,
    summary="[PRO-B-23] 전략 기반 상태 전환 (Archive 시 보관함 격리)",
)
def apply_transition(
    task_id: int = Path(..., description="과업 ID"),
    body: TransitionRequest = ...,
) -> TransitionResponse:
    """
    strategy_select에 매핑되는 상태로 DB 레코드를 업데이트한다.
    Archive 선택 시 메인 테이블에서 삭제하고 보관함 테이블로 이동한다.
    모든 전환은 상태 변경 이력(task_status_history)에 기록된다.
    """
    service = _get_service()
    try:
        return service.apply_transition(task_id, body)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ── 2. 보관함 목록 조회 ──────────────────────────────────────

@router.get(
    "/users/{user_id}/archives",
    response_model=ArchiveListResponse,
    summary="[PRO-B-23] 사용자 보관함 목록 조회",
)
def get_user_archives(
    user_id: str = Path(..., description="사용자 식별자"),
) -> ArchiveListResponse:
    """보관함 테이블에서 해당 사용자의 보관된 과업을 조회한다."""
    service = _get_service()
    archives = service.get_user_archives(user_id)
    items = [ArchiveItemResponse.model_validate(a) for a in archives]
    return ArchiveListResponse(
        user_id=user_id,
        total_count=len(items),
        archives=items,
        timestamp=datetime.now(timezone.utc),
    )


# ── 3. 상태 변경 이력 조회 ───────────────────────────────────

@router.get(
    "/tasks/{task_id}/history",
    response_model=StatusHistoryListResponse,
    summary="[PRO-B-23] 과업 상태 변경 이력 조회",
)
def get_task_status_history(
    task_id: int = Path(..., description="과업 ID"),
) -> StatusHistoryListResponse:
    """해당 과업의 모든 상태 전환 기록을 시간순으로 반환한다."""
    service = _get_service()
    history = service.get_task_history(task_id)
    items = [StatusHistoryItemResponse.model_validate(h) for h in history]
    return StatusHistoryListResponse(
        task_id=task_id,
        total_count=len(items),
        history=items,
        timestamp=datetime.now(timezone.utc),
    )
