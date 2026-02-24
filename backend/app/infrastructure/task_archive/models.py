"""
보관함 및 상태 변경 이력 모델 [PRO-B-23].
TaskArchive: 메인 테이블에서 격리된 보관 전용 테이블.
TaskStatusHistory: 과업 상태 전환 감사 추적(audit trail) 테이블.
"""
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text, func

from app.core.database import Base


class TaskArchive(Base):
    """보관함 테이블 [PRO-B-23]. 메인 tasks 테이블에서 격리된 보관 과업을 저장한다."""

    __tablename__ = "task_archives"

    id = Column(Integer, primary_key=True, autoincrement=True)
    original_task_id = Column(Integer, nullable=False, unique=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    original_status = Column(String(32), nullable=False)
    user_id = Column(String(64), nullable=False, index=True)
    due_date = Column(DateTime, nullable=False)
    task_created_at = Column(DateTime, nullable=False)
    archived_at = Column(DateTime, nullable=False, server_default=func.now())


class TaskStatusHistory(Base):
    """상태 변경 이력 테이블 [PRO-B-23]. 모든 상태 전환을 기록하여 데이터 정합성을 보장한다."""

    __tablename__ = "task_status_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, nullable=False, index=True)
    previous_status = Column(String(32), nullable=False)
    new_status = Column(String(32), nullable=False)
    strategy_applied = Column(String(32), nullable=True)
    changed_at = Column(DateTime, nullable=False, server_default=func.now())
