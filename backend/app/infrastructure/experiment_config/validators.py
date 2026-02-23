"""
운영 제약 검증 모듈 [PRO-B-22].
파라미터로 관리되는 상한값/임계값을 기반으로 비즈니스 제약을 검증한다.
"""
import logging
from dataclasses import dataclass

from sqlalchemy import func as sqlfunc

from app.core.database import get_session_factory
from app.infrastructure.experiment_config.config import ExperimentConfig
from app.infrastructure.task_archive.models import TaskArchive
from app.infrastructure.task_miss.service import TaskMissServiceImpl

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ValidationResult:
    """검증 결과."""

    valid: bool
    message: str
    current_value: int | float
    limit_value: int | float


class OperationalValidator:
    """[PRO-B-22] 운영 제약 검증기. 파라미터 변경이 즉시 반영된다."""

    @staticmethod
    def check_archive_limit(user_id: str) -> ValidationResult:
        """사용자의 보관함 레코드 수가 MAX_ARCHIVE_LIMIT을 초과하는지 검증한다."""
        limit = ExperimentConfig.max_archive_limit()
        session_factory = get_session_factory()
        with session_factory() as session:
            count = (
                session.query(sqlfunc.count(TaskArchive.id))
                .filter(TaskArchive.user_id == user_id)
                .scalar()
            ) or 0

        valid = count < limit
        msg = "보관 가능" if valid else f"보관함 상한 초과 ({count}/{limit})"
        logger.debug("[PRO-B-22] 보관함 검증 user=%s count=%d limit=%d → %s", user_id, count, limit, msg)
        return ValidationResult(valid=valid, message=msg, current_value=count, limit_value=limit)

    @staticmethod
    def check_trigger_threshold(user_id: str) -> ValidationResult:
        """사용자의 누적 miss_count가 TRIGGER_MISS_THRESHOLD 이상인지 검증한다."""
        threshold = ExperimentConfig.trigger_miss_threshold()
        miss_service = TaskMissServiceImpl()
        count, _ = miss_service.get_cumulative_miss_count(user_id)

        triggered = count >= threshold
        msg = f"트리거 조건 충족 ({count}>={threshold})" if triggered else f"미충족 ({count}<{threshold})"
        return ValidationResult(valid=triggered, message=msg, current_value=count, limit_value=threshold)

    @staticmethod
    def validate_strategy_option(option: str) -> ValidationResult:
        """선택된 전략이 AVAILABLE_STRATEGY_OPTIONS에 포함되는지 검증한다."""
        options = ExperimentConfig.available_strategy_options()
        valid = option in options
        msg = f"유효한 전략: {option}" if valid else f"허용되지 않은 전략: {option} (허용: {options})"
        return ValidationResult(valid=valid, message=msg, current_value=0, limit_value=0)
