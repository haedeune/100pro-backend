"""
트리거 설정 서비스 구현체 [PRO-B-25].
TriggerSettings를 통해 파라미터를 읽고, DB를 업데이트하여
코드 배포 없이 실험·운영 변수를 실시간 제어한다.
"""
import logging
import time
from datetime import datetime, timezone

from sqlalchemy import func as sqlfunc

from app.core.database import get_session_factory
from app.infrastructure.task_archive.models import TaskArchive
from app.infrastructure.task_miss.service import TaskMissServiceImpl
from app.infrastructure.task_params.models import SystemParameter
from app.infrastructure.trigger_config.settings import TriggerSettings

logger = logging.getLogger(__name__)

# [PRO-B-25] 변경 가능한 파라미터 키 화이트리스트
_ALLOWED_KEYS = {
    "TRIGGER_MISS_THRESHOLD",
    "AVAILABLE_STRATEGY_OPTIONS",
    "POST_MISS_EXIT_WINDOW",
    "MAX_ARCHIVE_LIMIT",
    "EXP_PROB_B10_RATIO",
}


class TriggerConfigServiceImpl:
    """[PRO-B-25] 트리거 임계치·운영 변수 서비스 구현체."""

    def __init__(self) -> None:
        self._miss_service = TaskMissServiceImpl()

    def get_settings(self) -> dict:
        """[PRO-B-25] 현재 적용 중인 전체 설정값을 반환한다."""
        return TriggerSettings.as_dict()

    def check_trigger(self, user_id: str) -> dict:
        """
        [PRO-B-25] 누적 miss_count와 TRIGGER_MISS_THRESHOLD를 비교하여
        팝업 노출 여부를 판정하고, 관련 설정값을 함께 반환한다.
        """
        start_ns = time.perf_counter_ns()
        now = datetime.now(timezone.utc)

        count, _ = self._miss_service.get_cumulative_miss_count(user_id)
        threshold = TriggerSettings.trigger_miss_threshold()
        triggered = count >= threshold

        result = {
            "user_id": user_id,
            "miss_count": count,
            "threshold": threshold,
            "triggered": triggered,
            "available_strategies": TriggerSettings.available_strategy_options() if triggered else [],
            "exit_window_seconds": TriggerSettings.post_miss_exit_window(),
            "exp_b10_ratio": TriggerSettings.exp_b10_ratio(),
        }

        elapsed_ms = (time.perf_counter_ns() - start_ns) / 1_000_000
        logger.info(
            "[%s][PRO-B-25] 트리거 판정 user=%s miss=%d threshold=%d triggered=%s (%.3fms)",
            now.isoformat(timespec="milliseconds"),
            user_id, count, threshold, triggered, elapsed_ms,
        )
        return result

    def check_archive_capacity(self, user_id: str) -> dict:
        """[PRO-B-25] 보관함 적재 가능 여부를 MAX_ARCHIVE_LIMIT 기준으로 검증한다."""
        limit = TriggerSettings.max_archive_limit()
        session_factory = get_session_factory()
        with session_factory() as session:
            count = (
                session.query(sqlfunc.count(TaskArchive.id))
                .filter(TaskArchive.user_id == user_id)
                .scalar()
            ) or 0

        can_archive = count < limit
        return {
            "user_id": user_id,
            "current_count": count,
            "max_limit": limit,
            "can_archive": can_archive,
            "message": "보관 가능" if can_archive else f"보관함 상한 도달 ({count}/{limit})",
        }

    def update_parameter(self, key: str, value: str) -> dict:
        """
        [PRO-B-25] 파라미터 값을 업데이트하고 캐시를 즉시 갱신한다.
        허용된 키만 변경 가능하다.
        """
        if key not in _ALLOWED_KEYS:
            raise ValueError(f"[PRO-B-25] 변경 불가 파라미터: {key} (허용: {_ALLOWED_KEYS})")

        now = datetime.now(timezone.utc)
        session_factory = get_session_factory()

        with session_factory() as session:
            param = session.query(SystemParameter).filter(SystemParameter.key == key).first()
            if param is None:
                raise ValueError(f"파라미터를 찾을 수 없습니다: {key}")

            old_value = param.value
            param.value = value
            param.updated_at = now
            session.commit()

        TriggerSettings.refresh()

        logger.info("[%s][PRO-B-25] 파라미터 변경 %s: %s → %s", now.isoformat(timespec="milliseconds"), key, old_value, value)

        return {"key": key, "old_value": old_value, "new_value": value}
