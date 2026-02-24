"""
행동 트래킹 요청/응답 스키마 [PRO-B-24].
"""
import enum
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class EventType(str, enum.Enum):
    """추적 대상 이벤트 유형 [PRO-B-24]."""

    TASK_MISS = "task_miss"
    ARCHIVE = "archive"
    MODIFY = "modify"
    KEEP = "keep"
    COMPLETED = "completed"


# -- Requests --

class RecordEventRequest(BaseModel):
    """행동 이벤트 기록 요청 [PRO-B-24]."""

    task_id: int = Field(..., description="과업 ID")
    user_id: str = Field(..., description="사용자 식별자")
    event_type: EventType = Field(..., description="이벤트 유형")
    metadata: Optional[dict[str, Any]] = Field(None, description="추가 메타데이터 (JSON)")


# -- Responses --

class BehaviorLogResponse(BaseModel):
    """행동 로그 단건 응답 [PRO-B-24]."""

    id: int
    task_id: int
    user_id: str
    event_type: str
    experiment_id: str
    experiment_group: str
    event_at: datetime
    previous_event_at: Optional[datetime] = None
    latency_ms: Optional[float] = None
    metadata_json: Optional[str] = None

    model_config = {"from_attributes": True}


class BehaviorChainResponse(BaseModel):
    """task_id 기준 행동 체인 응답 [PRO-B-24]."""

    task_id: int
    total_events: int
    chain: list[BehaviorLogResponse] = Field(default_factory=list)
    total_latency_ms: Optional[float] = Field(None, description="첫 이벤트~마지막 이벤트 총 경과 시간(ms)")
    timestamp: datetime


class ExperimentInfoResponse(BaseModel):
    """사용자 실험 할당 정보 응답 [PRO-B-24]."""

    user_id: str
    experiment_id: str
    group: str = Field(..., description="treatment | control")
    hash_value: int
    assigned_at: datetime
    newly_assigned: bool = Field(..., description="이번 요청에서 신규 할당 여부")

    model_config = {"from_attributes": True}


class BranchedResponse(BaseModel):
    """실험군/대조군에 따른 분기 응답 [PRO-B-24]."""

    user_id: str
    experiment_id: str
    group: str
    response_variant: str = Field(..., description="적용된 응답 변형 (treatment_v1 | control_default)")
    payload: dict[str, Any] = Field(default_factory=dict, description="그룹별 분기된 응답 데이터")
    timestamp: datetime


class UserBehaviorSummaryResponse(BaseModel):
    """사용자별 행동 요약 응답 [PRO-B-24]."""

    user_id: str
    experiment_id: str
    experiment_group: str
    total_events: int
    event_type_counts: dict[str, int] = Field(default_factory=dict)
    avg_latency_ms: Optional[float] = None
    timestamp: datetime
