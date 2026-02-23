"""
TaskMiss 서비스 구현체 [PRO-B-10].
사용자별 task_miss 누적 횟수를 DB Aggregation으로 집계하고,
Redis에 user:{userId}:miss_count 키로 캐싱하여 성능을 최적화한다.
"""
import logging
import time
from datetime import datetime, timezone

from sqlalchemy import func as sqlfunc

from app.core.database import get_session_factory
from app.core.redis import get_redis
from app.domains.task.models import Task, TaskStatus

logger = logging.getLogger(__name__)

REDIS_KEY_PREFIX = "user:{user_id}:miss_count"
CACHE_TTL_SECONDS = 300


class TaskMissServiceImpl:
    """사용자별 task_miss 누적 횟수 조회 구현체."""

    def get_cumulative_miss_count(self, user_id: str) -> tuple[int, bool]:
        """
        Redis 캐시를 먼저 확인하고, 미스 시 DB에서 집계하여 캐시에 저장한다.
        Returns: (count, cached)
        """
        start_ns = time.perf_counter_ns()
        now = datetime.now(timezone.utc)

        cached_value = self._get_from_cache(user_id)
        if cached_value is not None:
            elapsed_ms = (time.perf_counter_ns() - start_ns) / 1_000_000
            logger.info(
                "[%s] miss_count 캐시 HIT user=%s count=%d (%.3fms)",
                now.isoformat(timespec="milliseconds"),
                user_id,
                cached_value,
                elapsed_ms,
            )
            return cached_value, True

        count = self._aggregate_from_db(user_id)
        self._set_cache(user_id, count)

        elapsed_ms = (time.perf_counter_ns() - start_ns) / 1_000_000
        logger.info(
            "[%s] miss_count DB 집계 user=%s count=%d (%.3fms)",
            now.isoformat(timespec="milliseconds"),
            user_id,
            count,
            elapsed_ms,
        )
        return count, False

    def refresh_cache(self, user_id: str) -> int:
        """DB에서 최신 카운트를 조회 후 캐시를 갱신한다."""
        count = self._aggregate_from_db(user_id)
        self._set_cache(user_id, count)
        return count

    @staticmethod
    def _aggregate_from_db(user_id: str) -> int:
        session_factory = get_session_factory()
        with session_factory() as session:
            result = (
                session.query(sqlfunc.count(Task.id))
                .filter(Task.user_id == user_id, Task.status == TaskStatus.TASK_MISS)
                .scalar()
            )
        return result or 0

    @staticmethod
    def _get_from_cache(user_id: str) -> int | None:
        client = get_redis()
        if client is None:
            return None
        try:
            value = client.get(REDIS_KEY_PREFIX.format(user_id=user_id))
            return int(value) if value is not None else None
        except Exception:
            logger.warning("Redis 캐시 조회 실패 user=%s", user_id, exc_info=True)
            return None

    @staticmethod
    def _set_cache(user_id: str, count: int) -> None:
        client = get_redis()
        if client is None:
            return
        try:
            client.setex(
                REDIS_KEY_PREFIX.format(user_id=user_id),
                CACHE_TTL_SECONDS,
                str(count),
            )
        except Exception:
            logger.warning("Redis 캐시 저장 실패 user=%s", user_id, exc_info=True)
