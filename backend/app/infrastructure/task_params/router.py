"""
파라미터 관리 API 라우터 [PRO-B-16].
대시보드에서 실험·임계치·정책 변수를 실시간으로 조회·수정할 수 있는 엔드포인트를 제공한다.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Path, Query

from app.infrastructure.task_params.registry import ParameterRegistry
from app.infrastructure.task_params.schemas import (
    CategorySummaryResponse,
    ParameterCacheResponse,
    ParameterListResponse,
    ParameterResponse,
    ParameterUpdateRequest,
)
from app.infrastructure.task_params.service import ParameterServiceImpl

router = APIRouter()

_service: ParameterServiceImpl | None = None


def _get_service() -> ParameterServiceImpl:
    global _service
    if _service is None:
        _service = ParameterServiceImpl()
    return _service


# ── 1. 전체 파라미터 조회 ─────────────────────────────────────

@router.get(
    "/",
    response_model=ParameterListResponse,
    summary="[PRO-B-16] 전체 파라미터 목록 조회",
)
def list_parameters() -> ParameterListResponse:
    """DB에 저장된 모든 시스템 파라미터를 반환한다."""
    service = _get_service()
    params = service.get_all()
    items = [ParameterResponse.model_validate(p) for p in params]
    return ParameterListResponse(
        total_count=len(items),
        parameters=items,
        timestamp=datetime.now(timezone.utc),
    )


# ── 2. 키 기반 단건 조회 ─────────────────────────────────────

@router.get(
    "/key/{key}",
    response_model=ParameterResponse,
    summary="[PRO-B-16] 파라미터 단건 조회",
)
def get_parameter(
    key: str = Path(..., description="파라미터 키"),
) -> ParameterResponse:
    """키로 파라미터를 조회한다."""
    service = _get_service()
    param = service.get_by_key(key)
    if param is None:
        raise HTTPException(status_code=404, detail=f"파라미터를 찾을 수 없습니다: {key}")
    return ParameterResponse.model_validate(param)


# ── 3. 카테고리별 조회 ───────────────────────────────────────

@router.get(
    "/category/{category}",
    response_model=CategorySummaryResponse,
    summary="[PRO-B-16] 카테고리별 파라미터 조회",
)
def get_by_category(
    category: str = Path(..., description="카테고리 (experiment | threshold | policy)"),
) -> CategorySummaryResponse:
    """특정 카테고리의 파라미터를 조회한다."""
    registry = ParameterRegistry()
    params = registry.get_by_category(category)
    return CategorySummaryResponse(
        category=category,
        parameters=params,
        count=len(params),
        timestamp=datetime.now(timezone.utc),
    )


# ── 4. 파라미터 값 수정 (대시보드용) ────────────────────────

@router.put(
    "/key/{key}",
    response_model=ParameterResponse,
    summary="[PRO-B-16] 파라미터 값 수정 (코드 배포 없이 실시간 반영)",
)
def update_parameter(
    key: str = Path(..., description="파라미터 키"),
    body: ParameterUpdateRequest = ...,
) -> ParameterResponse:
    """
    파라미터 값을 수정한다. DB 업데이트 후 인메모리 캐시를 즉시 갱신하여
    코드 배포 없이 실시간으로 반영된다.
    """
    service = _get_service()
    try:
        param = service.update(key, body)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return ParameterResponse.model_validate(param)


# ── 5. 캐시 현황 조회 ────────────────────────────────────────

@router.get(
    "/cache",
    response_model=ParameterCacheResponse,
    summary="[PRO-B-16] 현재 인메모리 캐시 상태 조회",
)
def get_cache_status() -> ParameterCacheResponse:
    """현재 레지스트리 캐시에 로드된 파라미터 상태를 반환한다."""
    registry = ParameterRegistry()
    all_params = registry.get_all()
    return ParameterCacheResponse(
        total_count=len(all_params),
        parameters=all_params,
        timestamp=datetime.now(timezone.utc),
    )


# ── 6. 캐시 강제 갱신 ────────────────────────────────────────

@router.post(
    "/cache/refresh",
    response_model=ParameterCacheResponse,
    summary="[PRO-B-16] 인메모리 캐시 강제 갱신",
)
def refresh_cache() -> ParameterCacheResponse:
    """DB에서 파라미터를 재조회하여 캐시를 즉시 갱신한다."""
    registry = ParameterRegistry()
    registry.force_refresh()
    all_params = registry.get_all()
    return ParameterCacheResponse(
        total_count=len(all_params),
        parameters=all_params,
        timestamp=datetime.now(timezone.utc),
    )
