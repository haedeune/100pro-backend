"""
기한 만료 과업 자동 감지 및 task_miss 상태 전환 배치 스케줄러 [PRO-B-10].
APScheduler IntervalTrigger를 사용하여 주기적으로 미완료·기한 초과 과업을 탐색하고 상태를 전환한다.
전환 시 해당 사용자의 Redis 캐시를 무효화하여 실시간 집계 정합성을 보장한다.
"""
import logging
import time
from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import update

from app.core.database import get_session_factory
from app.core.redis import get_redis
from app.domains.task.models import Task, TaskStatus

logger = logging.getLogger(__name__)

MISS_CHECK_INTERVAL_SECONDS = 60
REDIS_KEY_PREFIX = "user:{user_id}:miss_count"


def _transition_expired_tasks() -> int:
    """
    due_date < 현재시각 이면서 완료·task_miss가 아닌 과업을 task_miss로 전환한다.
    전환된 행의 수를 반환하며, 영향받은 사용자의 Redis 캐시를 무효화한다.
    """
    start_ns = time.perf_counter_ns()
    now = datetime.now(timezone.utc)
    session_factory = get_session_factory()

    with session_factory() as session:
        affected_users = (
            session.query(Task.user_id)
            .filter(
                Task.due_date < now,
                Task.status.notin_([TaskStatus.COMPLETED, TaskStatus.TASK_MISS]),
            )
            .distinct()
            .all()
        )
        affected_user_ids = [row[0] for row in affected_users]

        if not affected_user_ids:
            elapsed_ms = (time.perf_counter_ns() - start_ns) / 1_000_000
            logger.info(
                "[%s] task_miss 전환 대상 없음 (%.3fms)",
                now.isoformat(timespec="milliseconds"),
                elapsed_ms,
            )
            return 0

        result = session.execute(
            update(Task)
            .where(
                Task.due_date < now,
                Task.status.notin_([TaskStatus.COMPLETED, TaskStatus.TASK_MISS]),
            )
            .values(status=TaskStatus.TASK_MISS, updated_at=now)
        )
        transitioned = result.rowcount  # type: ignore[union-attr]
        session.commit()

    _invalidate_redis_cache(affected_user_ids)

    elapsed_ms = (time.perf_counter_ns() - start_ns) / 1_000_000
    logger.info(
        "[%s] task_miss 전환 완료: %d건, 영향 사용자: %s (%.3fms)",
        now.isoformat(timespec="milliseconds"),
        transitioned,
        affected_user_ids,
        elapsed_ms,
    )
    return transitioned


def _invalidate_redis_cache(user_ids: list[str]) -> None:
    """전환된 사용자의 누적 miss_count 캐시를 삭제한다."""
    client = get_redis()
    if client is None:
        return
    keys = [REDIS_KEY_PREFIX.format(user_id=uid) for uid in user_ids]
    try:
        client.delete(*keys)
        logger.debug("Redis 캐시 무효화: %s", keys)
    except Exception:
        logger.warning("Redis 캐시 무효화 실패", exc_info=True)


class TaskMissScheduler:
    """task_miss 상태 전환을 주기적으로 수행하는 스케줄러 래퍼."""

    def __init__(self, interval_seconds: int = MISS_CHECK_INTERVAL_SECONDS) -> None:
        self._scheduler = BackgroundScheduler(daemon=True)
        self._interval = interval_seconds

    def start(self) -> None:
        self._scheduler.add_job(
            _transition_expired_tasks,
            trigger="interval",
            seconds=self._interval,
            id="task_miss_transition",
            replace_existing=True,
            next_run_time=datetime.now(timezone.utc),
        )
        self._scheduler.start()
        logger.info("TaskMissScheduler 시작 (주기: %ds)", self._interval)

    def shutdown(self) -> None:
        self._scheduler.shutdown(wait=False)
        logger.info("TaskMissScheduler 종료")

    @staticmethod
    def run_now() -> int:
        """즉시 1회 실행하여 전환 건수를 반환한다. API 수동 트리거용."""
        return _transition_expired_tasks()
