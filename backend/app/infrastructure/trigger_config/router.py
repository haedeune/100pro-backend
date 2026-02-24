"""
트리거 설정 API 라우터 [PRO-B-25].
실험 트리거 임계치 조회, 판정, 보관함 검증, 파라미터 실시간 변경 엔드포인트를 제공한다.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Path

from app.infrastructure.trigger_config.schemas import (
    ArchiveLimitCheckResponse,
    ParameterUpdateRequest,
    ParameterUpdateResponse,
    TriggerCheckResponse,
    TriggerSettingsResponse,
)
from app.infrastructure.trigger_config.service import TriggerConfigServiceImpl

router = APIRouter()

_service: TriggerConfigServiceImpl | None = None


def _get_service() -> TriggerConfigServiceImpl:
    global _service
    if _service is None:
        _service = TriggerConfigServiceImpl()
    return _service


# ── 1. 현재 설정 현황 ────────────────────────────────────────

@router.get(
    "/",
    response_model=TriggerSettingsResponse,
    summary="[PRO-B-25] 트리거·운영 설정 현황 조회",
)
def get_settings() -> TriggerSettingsResponse:
    """현재 적용 중인 TRIGGER_MISS_THRESHOLD 등 전체 설정값을 반환한다."""
    service = _get_service()
    return TriggerSettingsResponse(
        settings=service.get_settings(),
        timestamp=datetime.now(timezone.utc),
    )


# ── 2. 트리거 판정 ───────────────────────────────────────────

@router.get(
    "/users/{user_id}/trigger-check",
    response_model=TriggerCheckResponse,
    summary="[PRO-B-25] 사용자 트리거 임계치 판정",
)
def check_trigger(
    user_id: str = Path(..., description="사용자 식별자"),
) -> TriggerCheckResponse:
    """
    누적 실패 수와 TRIGGER_MISS_THRESHOLD를 비교하여 개입 시점을 판정한다.
    충족 시 AVAILABLE_STRATEGY_OPTIONS를 함께 반환한다.
    """
    service = _get_service()
    result = service.check_trigger(user_id)
    return TriggerCheckResponse(**result, timestamp=datetime.now(timezone.utc))


# ── 3. 보관함 상한 검증 ──────────────────────────────────────

@router.get(
    "/users/{user_id}/archive-capacity",
    response_model=ArchiveLimitCheckResponse,
    summary="[PRO-B-25] 보관함 적재 가능 여부 검증",
)
def check_archive_capacity(
    user_id: str = Path(..., description="사용자 식별자"),
) -> ArchiveLimitCheckResponse:
    """MAX_ARCHIVE_LIMIT 기준으로 보관함 적재 가능 여부를 반환한다."""
    service = _get_service()
    result = service.check_archive_capacity(user_id)
    return ArchiveLimitCheckResponse(**result, timestamp=datetime.now(timezone.utc))


# ── 4. 파라미터 실시간 변경 ──────────────────────────────────

@router.put(
    "/key/{key}",
    response_model=ParameterUpdateResponse,
    summary="[PRO-B-25] 파라미터 실시간 변경 (코드 배포 불필요)",
)
def update_parameter(
    key: str = Path(..., description="파라미터 키"),
    body: ParameterUpdateRequest = ...,
) -> ParameterUpdateResponse:
    """
    파라미터 값을 변경하고 인메모리 캐시를 즉시 갱신한다.
    PRO-B-25 허용 키: TRIGGER_MISS_THRESHOLD, AVAILABLE_STRATEGY_OPTIONS,
    POST_MISS_EXIT_WINDOW, MAX_ARCHIVE_LIMIT, EXP_PROB_B10_RATIO
    """
    service = _get_service()
    try:
        result = service.update_parameter(key, body.value)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return ParameterUpdateResponse(**result, timestamp=datetime.now(timezone.utc))
