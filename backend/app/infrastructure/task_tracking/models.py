"""
행동 체인 로그 및 실험 할당 모델 [PRO-B-24].
BehaviorLog: task_id 기준으로 '실패→보관→성공' 과정을 ms 단위로 추적한다.
ExperimentAssignment: 사용자별 실험군/대조군 할당을 영구 저장한다.
"""
from sqlalchemy import Column, DateTime, Float, Integer, String, Text, func

from app.core.database import Base


class BehaviorLog(Base):
    """
    행동 체인 로그 테이블 [PRO-B-24].
    task_id를 외래키 역할로 활용하여 과업 상태 변화를 시간 순으로 기록한다.
    모든 로그에 Experiment ID가 자동 결합된다.
    """

    __tablename__ = "behavior_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, nullable=False, index=True)
    user_id = Column(String(64), nullable=False, index=True)
    event_type = Column(String(32), nullable=False, index=True)
    experiment_id = Column(String(64), nullable=False, index=True)
    experiment_group = Column(String(16), nullable=False)
    event_at = Column(DateTime, nullable=False)
    previous_event_at = Column(DateTime, nullable=True)
    latency_ms = Column(Float, nullable=True)
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())


class ExperimentAssignment(Base):
    """
    실험군 할당 영구 저장 테이블 [PRO-B-24].
    동일 사용자는 항상 같은 그룹에 할당되도록 결과를 보존한다.
    """

    __tablename__ = "experiment_assignments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(64), nullable=False, unique=True, index=True)
    experiment_id = Column(String(64), nullable=False)
    group = Column(String(16), nullable=False)
    hash_value = Column(Integer, nullable=False)
    assigned_at = Column(DateTime, nullable=False, server_default=func.now())
