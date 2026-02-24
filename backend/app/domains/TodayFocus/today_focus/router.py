"""
TodayFocus API 라우터 [PM-TF-PAR-01].
홈 화면 할 일 조회(TaskDisplayScope 적용) 엔드포인트를 제공한다.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Path

from app.domains.task.schemas import TaskResponse
from app.domains.TodayFocus.today_focus.service import TodayFocusServiceImpl
from app.infrastructure.task_strategy.schemas import ActiveTaskListResponse

router = APIRouter()

_today_focus_service: TodayFocusServiceImpl | None = None


def _get_today_focus_service() -> TodayFocusServiceImpl:
    global _today_focus_service
    if _today_focus_service is None:
        _today_focus_service = TodayFocusServiceImpl()
    return _today_focus_service


@router.get(
    "/users/{user_id}/active-tasks",
    response_model=ActiveTaskListResponse,
    summary="[PRO-B-21] 활성 과업 목록 조회 (보관 제외, PM-TF-PAR-01 today 범위 적용)",
)
def get_active_tasks(
    user_id: str = Path(..., description="사용자 식별자"),
) -> ActiveTaskListResponse:
    """TaskDisplayScope(today)에 따라 홈에 표시할 과업만 반환. 오늘 할 일 없으면 빈 리스트."""
    service = _get_today_focus_service()
    tasks = service.get_home_tasks(user_id)
    task_dtos = [TaskResponse.model_validate(t) for t in tasks]
    return ActiveTaskListResponse(
        user_id=user_id,
        total_count=len(task_dtos),
        tasks=task_dtos,
        timestamp=datetime.now(timezone.utc),
    )
