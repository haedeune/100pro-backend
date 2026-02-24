"""
행동 트래킹 서비스 구현체 [PRO-B-24].
모든 과업 이벤트를 BehaviorLog에 기록하며, 이때:
1. 직전 이벤트와의 시간 간격(latency_ms)을 자동 계산한다.
2. 사용자의 실험 할당 정보(experiment_id, group)를 자동 결합한다.
"""
import json
import logging
import time
from datetime import datetime, timezone

from sqlalchemy import func as sqlfunc

from app.core.database import get_session_factory
from app.infrastructure.task_tracking.experiment import PersistentExperimentAssigner
from app.infrastructure.task_tracking.models import BehaviorLog
from app.infrastructure.task_tracking.schemas import RecordEventRequest

logger = logging.getLogger(__name__)


class BehaviorTrackingServiceImpl:
    """행동 체인 트래킹 + 실험 결합 구현체 [PRO-B-24]."""

    def record_event(self, request: RecordEventRequest) -> BehaviorLog:
        """
        이벤트를 기록한다.
        - 동일 task_id의 직전 이벤트를 조회하여 latency_ms를 계산한다.
        - 사용자 실험 할당 정보를 자동으로 결합한다.
        """
        start_ns = time.perf_counter_ns()
        now = datetime.now(timezone.utc)
        session_factory = get_session_factory()

        with session_factory() as session:
            # [PRO-B-24] 실험군 할당 조회/생성 (모든 로그에 experiment_id 결합)
            assignment = PersistentExperimentAssigner.get_or_assign(session, request.user_id)

            # [PRO-B-24] 직전 이벤트 조회 → latency 계산
            prev_log = (
                session.query(BehaviorLog)
                .filter(BehaviorLog.task_id == request.task_id)
                .order_by(BehaviorLog.event_at.desc())
                .first()
            )

            previous_event_at = prev_log.event_at if prev_log else None
            latency_ms = None
            if previous_event_at is not None:
                delta = now - previous_event_at
                latency_ms = round(delta.total_seconds() * 1000, 3)

            metadata_str = json.dumps(request.metadata, ensure_ascii=False) if request.metadata else None

            log_entry = BehaviorLog(
                task_id=request.task_id,
                user_id=request.user_id,
                event_type=request.event_type.value,
                experiment_id=assignment.experiment_id,
                experiment_group=assignment.group,
                event_at=now,
                previous_event_at=previous_event_at,
                latency_ms=latency_ms,
                metadata_json=metadata_str,
            )
            session.add(log_entry)
            session.commit()
            session.refresh(log_entry)

            elapsed_ms = (time.perf_counter_ns() - start_ns) / 1_000_000
            logger.info(
                "[%s][PRO-B-24] 이벤트 기록 task=%d user=%s event=%s "
                "experiment=%s group=%s latency=%.3fms (처리: %.3fms)",
                now.isoformat(timespec="milliseconds"),
                request.task_id,
                request.user_id,
                request.event_type.value,
                assignment.experiment_id,
                assignment.group,
                latency_ms or 0,
                elapsed_ms,
            )

            session.expunge(log_entry)

        return log_entry

    def get_behavior_chain(self, task_id: int) -> list[BehaviorLog]:
        """task_id 기준으로 시간순 행동 체인을 반환한다."""
        session_factory = get_session_factory()
        with session_factory() as session:
            logs = (
                session.query(BehaviorLog)
                .filter(BehaviorLog.task_id == task_id)
                .order_by(BehaviorLog.event_at.asc())
                .all()
            )
            session.expunge_all()
        return logs

    def get_user_summary(self, user_id: str) -> dict:
        """사용자별 이벤트 유형 카운트, 평균 latency, 실험 정보 요약."""
        session_factory = get_session_factory()
        with session_factory() as session:
            assignment = PersistentExperimentAssigner.get_or_assign(session, user_id)

            rows = (
                session.query(
                    BehaviorLog.event_type,
                    sqlfunc.count(BehaviorLog.id),
                )
                .filter(BehaviorLog.user_id == user_id)
                .group_by(BehaviorLog.event_type)
                .all()
            )
            event_counts = {row[0]: row[1] for row in rows}
            total = sum(event_counts.values())

            avg_row = (
                session.query(sqlfunc.avg(BehaviorLog.latency_ms))
                .filter(BehaviorLog.user_id == user_id, BehaviorLog.latency_ms.isnot(None))
                .scalar()
            )
            avg_latency = round(float(avg_row), 3) if avg_row is not None else None

            session.commit()

        return {
            "experiment_id": assignment.experiment_id,
            "experiment_group": assignment.group,
            "total_events": total,
            "event_type_counts": event_counts,
            "avg_latency_ms": avg_latency,
        }
