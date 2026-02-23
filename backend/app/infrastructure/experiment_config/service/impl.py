"""
실험 설정 서비스 구현체 [PRO-B-22].
ExperimentConfig 래퍼와 OperationalValidator를 조합하여
트리거 판정 + 전략 옵션 제공 + 운영 제약 검증을 수행한다.
"""
import logging
import time
from datetime import datetime, timezone

from app.infrastructure.experiment_config.config import ExperimentConfig
from app.infrastructure.experiment_config.validators import OperationalValidator, ValidationResult
from app.infrastructure.task_miss.service import TaskMissServiceImpl

logger = logging.getLogger(__name__)


class ExperimentConfigServiceImpl:
    """[PRO-B-22] 실험 설정 조회 + 운영 검증 구현체."""

    def __init__(self) -> None:
        self._miss_service = TaskMissServiceImpl()

    def get_current_config(self) -> dict:
        """현재 적용 중인 모든 실험·운영 설정값을 반환한다."""
        return ExperimentConfig.as_dict()

    def check_trigger(self, user_id: str) -> dict:
        """
        [PRO-B-22] 사용자의 트리거 임계치 충족 여부를 판정하고,
        충족 시 제공 가능한 전략 옵션 목록을 함께 반환한다.
        """
        start_ns = time.perf_counter_ns()
        now = datetime.now(timezone.utc)

        count, _ = self._miss_service.get_cumulative_miss_count(user_id)
        threshold = ExperimentConfig.trigger_miss_threshold()
        triggered = count >= threshold

        result = {
            "user_id": user_id,
            "miss_count": count,
            "threshold": threshold,
            "triggered": triggered,
            "experiment_active": ExperimentConfig.is_experiment_active(),
            "available_strategies": ExperimentConfig.available_strategy_options() if triggered else [],
        }

        elapsed_ms = (time.perf_counter_ns() - start_ns) / 1_000_000
        logger.info(
            "[%s][PRO-B-22] 트리거 판정 user=%s miss=%d threshold=%d triggered=%s (%.3fms)",
            now.isoformat(timespec="milliseconds"),
            user_id, count, threshold, triggered, elapsed_ms,
        )
        return result

    def check_archive_limit(self, user_id: str) -> ValidationResult:
        return OperationalValidator.check_archive_limit(user_id)

    def validate_strategy(self, option: str) -> ValidationResult:
        return OperationalValidator.validate_strategy_option(option)
