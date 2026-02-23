"""
실험 설정 요청/응답 스키마 [PRO-B-22].
"""
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class ExperimentConfigResponse(BaseModel):
    """[PRO-B-22] 전체 실험·운영 설정 현황 응답."""

    config: dict[str, Any] = Field(..., description="현재 적용 중인 설정값")
    timestamp: datetime


class ValidationResultResponse(BaseModel):
    """[PRO-B-22] 운영 제약 검증 결과 응답."""

    check_type: str
    user_id: Optional[str] = None
    valid: bool
    message: str
    current_value: float
    limit_value: float
    timestamp: datetime


class StrategyOptionsResponse(BaseModel):
    """[PRO-B-22] 현재 제공 가능한 전략 옵션 목록."""

    options: list[str]
    count: int
    timestamp: datetime


class TriggerCheckResponse(BaseModel):
    """[PRO-B-22] 트리거 임계치 충족 여부 + 전략 옵션 통합 응답."""

    user_id: str
    miss_count: int
    threshold: int
    triggered: bool
    experiment_active: bool
    available_strategies: list[str]
    timestamp: datetime
