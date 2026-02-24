"""
파라미터 관리 요청/응답 스키마 [PRO-B-16].
"""
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class ParameterResponse(BaseModel):
    """파라미터 단건 응답 [PRO-B-16]."""

    key: str
    value: str
    value_type: str
    category: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ParameterUpdateRequest(BaseModel):
    """파라미터 값 수정 요청 [PRO-B-16]."""

    value: str = Field(..., description="새로운 값 (문자열로 전달, 타입은 기존 value_type에 따라 검증)")
    description: Optional[str] = Field(None, description="설명 업데이트 (null이면 기존 유지)")


class ParameterListResponse(BaseModel):
    """파라미터 목록 응답 [PRO-B-16]."""

    total_count: int
    parameters: list[ParameterResponse] = Field(default_factory=list)
    timestamp: datetime


class ParameterCacheResponse(BaseModel):
    """현재 캐시 상태 응답 [PRO-B-16]."""

    total_count: int
    parameters: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime


class CategorySummaryResponse(BaseModel):
    """카테고리별 파라미터 요약 [PRO-B-16]."""

    category: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    count: int
    timestamp: datetime
