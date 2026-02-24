"""
DB 영구 실험군 할당 로직 [PRO-B-24].
SHA-256 해시 기반으로 사용자를 결정론적(deterministic)으로 할당하고,
결과를 experiment_assignments 테이블에 영구 저장한다.
이미 할당된 사용자는 DB에서 조회하여 동일 그룹을 반환한다.
"""
import hashlib
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.infrastructure.task_tracking.models import ExperimentAssignment

logger = logging.getLogger(__name__)

TREATMENT_GROUP = "treatment"
CONTROL_GROUP = "control"
DEFAULT_EXPERIMENT_ID = "PRO-B-24-ab-test"
DEFAULT_RATIO = 50


@dataclass(frozen=True)
class PersistentAssignmentResult:
    """실험 할당 결과 [PRO-B-24]."""

    user_id: str
    experiment_id: str
    group: str
    hash_value: int
    assigned_at: datetime
    newly_assigned: bool


class PersistentExperimentAssigner:
    """
    DB 영구 저장 실험군 할당기 [PRO-B-24].
    동일 사용자에게 항상 같은 그룹을 보장한다.
    """

    @staticmethod
    def get_or_assign(session: Session, user_id: str) -> PersistentAssignmentResult:
        """기존 할당이 있으면 조회, 없으면 신규 할당 후 저장한다."""
        existing = (
            session.query(ExperimentAssignment)
            .filter(ExperimentAssignment.user_id == user_id)
            .first()
        )
        if existing is not None:
            return PersistentAssignmentResult(
                user_id=existing.user_id,
                experiment_id=existing.experiment_id,
                group=existing.group,
                hash_value=existing.hash_value,
                assigned_at=existing.assigned_at,
                newly_assigned=False,
            )

        experiment_id = os.getenv("EXPERIMENT_ID", DEFAULT_EXPERIMENT_ID)
        ratio = int(os.getenv("EXPERIMENT_RATIO", str(DEFAULT_RATIO)))
        hash_value = PersistentExperimentAssigner._compute_hash(user_id)
        group = TREATMENT_GROUP if (hash_value % 100) < ratio else CONTROL_GROUP
        now = datetime.now(timezone.utc)

        assignment = ExperimentAssignment(
            user_id=user_id,
            experiment_id=experiment_id,
            group=group,
            hash_value=hash_value,
            assigned_at=now,
        )
        session.add(assignment)
        session.flush()

        logger.info(
            "[%s][PRO-B-24] 신규 실험 할당 user=%s group=%s hash=%d experiment=%s",
            now.isoformat(timespec="milliseconds"),
            user_id,
            group,
            hash_value,
            experiment_id,
        )

        return PersistentAssignmentResult(
            user_id=user_id,
            experiment_id=experiment_id,
            group=group,
            hash_value=hash_value,
            assigned_at=now,
            newly_assigned=True,
        )

    @staticmethod
    def _compute_hash(user_id: str) -> int:
        """SHA-256 해시의 마지막 4바이트를 부호 없는 정수로 변환한다."""
        digest = hashlib.sha256(user_id.encode("utf-8")).digest()
        return int.from_bytes(digest[-4:], byteorder="big")
