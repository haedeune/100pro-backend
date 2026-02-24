"""
보관함 및 상태 전환 요청/응답 스키마 [PRO-B-23].
"""
import enum
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class StrategyType(str, enum.Enum):
    """전략 선택 열거형 [PRO-B-23]."""

    ARCHIVE = "archive"
    MODIFY = "modify"
    KEEP = "keep"


# -- Requests --

class TransitionRequest(BaseModel):
    """상태 전환 요청 [PRO-B-23]."""

    strategy_select: StrategyType = Field(..., description="전략 (archive | modify | keep)")
    new_due_date: Optional[datetime] = Field(
        None,
        description="modify 시 새로운 기한 (archive·keep 시 무시)",
    )


# -- Responses --

class TransitionResponse(BaseModel):
    """상태 전환 결과 응답 [PRO-B-23]."""

    task_id: int
    previous_status: str
    current_status: str
    strategy_applied: StrategyType
    archived: bool = Field(..., description="보관함 테이블로 이동 여부")
    history_id: int = Field(..., description="기록된 상태 변경 이력 ID")
    timestamp: datetime


class ArchiveItemResponse(BaseModel):
    """보관함 단건 응답 [PRO-B-23]."""

    id: int
    original_task_id: int
    title: str
    description: Optional[str] = None
    original_status: str
    user_id: str
    due_date: datetime
    task_created_at: datetime
    archived_at: datetime

    model_config = {"from_attributes": True}


class ArchiveListResponse(BaseModel):
    """보관함 목록 응답 [PRO-B-23]."""

    user_id: str
    total_count: int
    archives: list[ArchiveItemResponse] = Field(default_factory=list)
    timestamp: datetime


class StatusHistoryItemResponse(BaseModel):
    """상태 변경 이력 단건 [PRO-B-23]."""

    id: int
    task_id: int
    previous_status: str
    new_status: str
    strategy_applied: Optional[str] = None
    changed_at: datetime

    model_config = {"from_attributes": True}


class StatusHistoryListResponse(BaseModel):
    """상태 변경 이력 목록 응답 [PRO-B-23]."""

    task_id: int
    total_count: int
    history: list[StatusHistoryItemResponse] = Field(default_factory=list)
    timestamp: datetime
