"""
전략 선택 요청/응답 스키마 [PRO-B-21].
"""
import enum
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class StrategySelect(str, enum.Enum):
    """사용자가 선택할 수 있는 전략."""

    ARCHIVE = "archive"
    MODIFY = "modify"
    KEEP = "keep"


# -- Requests --

class ApplyStrategyRequest(BaseModel):
    """전략 적용 요청."""

    strategy_select: StrategySelect = Field(..., description="선택한 전략 (archive | modify | keep)")
    new_due_date: Optional[datetime] = Field(
        None,
        description="modify 전략 선택 시 새로운 기한 (archive·keep 시 무시됨)",
    )


# -- Responses --

class ApplyStrategyResponse(BaseModel):
    """전략 적용 결과 응답."""

    task_id: int
    previous_status: str
    current_status: str
    strategy_applied: StrategySelect
    is_archived: bool
    timestamp: datetime = Field(..., description="처리 시각 (ms 정밀도)")


class ExperimentAssignmentResponse(BaseModel):
    """실험군/대조군 할당 결과 응답."""

    user_id: str
    cumulative_miss_count: int = Field(..., description="누적 task_miss 횟수")
    trigger_threshold: int = Field(..., description="실험 노출 임계값")
    eligible: bool = Field(..., description="임계값 충족 여부")
    feature_flag_enabled: bool = Field(..., description="Feature Flag 활성 상태")
    group: Optional[str] = Field(
        None,
        description="할당된 그룹 (experiment | control). 미자격·비활성 시 null",
    )
    timestamp: datetime


class ActiveTaskListResponse(BaseModel):
    """활성 과업 목록 응답 (보관된 과업 제외)."""

    user_id: str
    total_count: int
    tasks: list = Field(default_factory=list, description="TaskResponse 목록")
    timestamp: datetime
