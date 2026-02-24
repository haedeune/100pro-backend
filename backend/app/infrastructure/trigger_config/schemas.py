"""
트리거 설정 요청/응답 스키마 [PRO-B-25].
"""
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class TriggerSettingsResponse(BaseModel):
    """[PRO-B-25] 전체 트리거·운영 설정 현황."""

    settings: dict[str, Any] = Field(..., description="현재 적용 중인 설정값")
    timestamp: datetime


class TriggerCheckResponse(BaseModel):
    """[PRO-B-25] 사용자 트리거 판정 결과."""

    user_id: str
    miss_count: int
    threshold: int
    triggered: bool
    available_strategies: list[str]
    exit_window_seconds: int
    exp_b10_ratio: float
    timestamp: datetime


class ParameterUpdateRequest(BaseModel):
    """[PRO-B-25] 파라미터 값 변경 요청."""

    value: str = Field(..., description="새로운 값 (문자열)")


class ParameterUpdateResponse(BaseModel):
    """[PRO-B-25] 파라미터 변경 결과."""

    key: str
    old_value: str
    new_value: str
    timestamp: datetime


class ArchiveLimitCheckResponse(BaseModel):
    """[PRO-B-25] 보관함 상한 검증 결과."""

    user_id: str
    current_count: int
    max_limit: int
    can_archive: bool
    message: str
    timestamp: datetime
