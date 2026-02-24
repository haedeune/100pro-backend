"""
실험 설정 API 라우터 [PRO-B-22].
실험·운영 파라미터 조회, 트리거 판정, 운영 제약 검증 엔드포인트를 제공한다.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Path, Query

from app.infrastructure.experiment_config.schemas import (
    ExperimentConfigResponse,
    StrategyOptionsResponse,
    TriggerCheckResponse,
    ValidationResultResponse,
)
from app.infrastructure.experiment_config.service import ExperimentConfigServiceImpl

router = APIRouter()

_service: ExperimentConfigServiceImpl | None = None


def _get_service() -> ExperimentConfigServiceImpl:
    global _service
    if _service is None:
        _service = ExperimentConfigServiceImpl()
    return _service


# ── 1. 현재 설정 현황 조회 ────────────────────────────────────

@router.get(
    "/",
    response_model=ExperimentConfigResponse,
    summary="[PRO-B-22] 실험·운영 설정 현황 조회",
)
def get_config() -> ExperimentConfigResponse:
    """현재 적용 중인 실험 임계치, 운영 상한, 전략 옵션 등을 반환한다."""
    service = _get_service()
    return ExperimentConfigResponse(
        config=service.get_current_config(),
        timestamp=datetime.now(timezone.utc),
    )


# ── 2. 전략 옵션 목록 조회 ───────────────────────────────────

@router.get(
    "/strategy-options",
    response_model=StrategyOptionsResponse,
    summary="[PRO-B-22] 현재 제공 가능한 전략 옵션 조회",
)
def get_strategy_options() -> StrategyOptionsResponse:
    """AVAILABLE_STRATEGY_OPTIONS 파라미터에서 읽어온 옵션 목록을 반환한다."""
    service = _get_service()
    config = service.get_current_config()
    options = config["AVAILABLE_STRATEGY_OPTIONS"]
    return StrategyOptionsResponse(
        options=options,
        count=len(options),
        timestamp=datetime.now(timezone.utc),
    )


# ── 3. 트리거 임계치 판정 ────────────────────────────────────

@router.get(
    "/users/{user_id}/trigger-check",
    response_model=TriggerCheckResponse,
    summary="[PRO-B-22] 사용자 트리거 임계치 충족 판정",
)
def check_trigger(
    user_id: str = Path(..., description="사용자 식별자"),
) -> TriggerCheckResponse:
    """
    누적 miss_count와 TRIGGER_MISS_THRESHOLD를 비교하여 팝업 노출 여부를 판정한다.
    충족 시 AVAILABLE_STRATEGY_OPTIONS를 함께 반환한다.
    """
    service = _get_service()
    result = service.check_trigger(user_id)
    return TriggerCheckResponse(
        **result,
        timestamp=datetime.now(timezone.utc),
    )


# ── 4. 보관함 상한 검증 ──────────────────────────────────────

@router.get(
    "/users/{user_id}/archive-limit-check",
    response_model=ValidationResultResponse,
    summary="[PRO-B-22] 보관함 상한 검증",
)
def check_archive_limit(
    user_id: str = Path(..., description="사용자 식별자"),
) -> ValidationResultResponse:
    """사용자의 보관함 레코드 수가 MAX_ARCHIVE_LIMIT 이내인지 검증한다."""
    service = _get_service()
    result = service.check_archive_limit(user_id)
    return ValidationResultResponse(
        check_type="archive_limit",
        user_id=user_id,
        valid=result.valid,
        message=result.message,
        current_value=result.current_value,
        limit_value=result.limit_value,
        timestamp=datetime.now(timezone.utc),
    )


# ── 5. 전략 옵션 유효성 검증 ─────────────────────────────────

@router.get(
    "/validate-strategy",
    response_model=ValidationResultResponse,
    summary="[PRO-B-22] 전략 옵션 유효성 검증",
)
def validate_strategy(
    option: str = Query(..., description="검증할 전략 이름 (예: Archive)"),
) -> ValidationResultResponse:
    """선택된 전략이 AVAILABLE_STRATEGY_OPTIONS에 포함되는지 검증한다."""
    service = _get_service()
    result = service.validate_strategy(option)
    return ValidationResultResponse(
        check_type="strategy_option",
        valid=result.valid,
        message=result.message,
        current_value=result.current_value,
        limit_value=result.limit_value,
        timestamp=datetime.now(timezone.utc),
    )
