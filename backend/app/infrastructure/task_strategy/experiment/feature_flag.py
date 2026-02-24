"""
Feature Flag 기반 실험군/대조군 할당 로직 [PRO-B-21].
사용자 고유 ID의 SHA-256 해시를 이용하여 결정론적(deterministic)으로
동일 사용자에게 항상 같은 그룹을 할당한다.
"""
import hashlib
import logging
from dataclasses import dataclass

from app.infrastructure.task_strategy.experiment.config import (
    get_experiment_ratio,
    get_trigger_miss_threshold,
    is_feature_flag_enabled,
)

logger = logging.getLogger(__name__)

EXPERIMENT_GROUP = "experiment"
CONTROL_GROUP = "control"


@dataclass(frozen=True)
class AssignmentResult:
    """실험 할당 결과."""

    user_id: str
    cumulative_miss_count: int
    trigger_threshold: int
    eligible: bool
    feature_flag_enabled: bool
    group: str | None


class ExperimentAssigner:
    """사용자별 실험군/대조군 할당기."""

    @staticmethod
    def assign(user_id: str, cumulative_miss_count: int) -> AssignmentResult:
        threshold = get_trigger_miss_threshold()
        flag_enabled = is_feature_flag_enabled()
        eligible = cumulative_miss_count >= threshold

        if not flag_enabled or not eligible:
            return AssignmentResult(
                user_id=user_id,
                cumulative_miss_count=cumulative_miss_count,
                trigger_threshold=threshold,
                eligible=eligible,
                feature_flag_enabled=flag_enabled,
                group=None,
            )

        group = ExperimentAssigner._hash_assign(user_id)
        logger.info(
            "[PRO-B-21] 실험 할당 user=%s miss=%d threshold=%d group=%s",
            user_id,
            cumulative_miss_count,
            threshold,
            group,
        )
        return AssignmentResult(
            user_id=user_id,
            cumulative_miss_count=cumulative_miss_count,
            trigger_threshold=threshold,
            eligible=True,
            feature_flag_enabled=True,
            group=group,
        )

    @staticmethod
    def _hash_assign(user_id: str) -> str:
        """SHA-256 해시의 마지막 4바이트를 정수로 변환하여 그룹을 결정한다."""
        digest = hashlib.sha256(user_id.encode("utf-8")).digest()
        value = int.from_bytes(digest[-4:], byteorder="big")
        ratio = get_experiment_ratio()
        return EXPERIMENT_GROUP if (value % 100) < ratio else CONTROL_GROUP
