"""
전략 서비스 구현체 [PRO-B-21].
strategy_select 값에 따라 과업 상태를 전환하고,
Archive 선택 시 is_archived=True로 설정하여 활성 리스트에서 제외한다.
"""
import logging
import time
from datetime import datetime, timezone

from sqlalchemy import and_

from app.core.database import get_session_factory
from app.core.redis import get_redis
from app.domains.task.models import Task, TaskStatus
from app.infrastructure.task_strategy.schemas import (
    ApplyStrategyRequest,
    ApplyStrategyResponse,
    StrategySelect,
)

logger = logging.getLogger(__name__)

REDIS_MISS_KEY = "user:{user_id}:miss_count"

# [PRO-B-21] strategy_select → TaskStatus 매핑
_STRATEGY_STATUS_MAP: dict[StrategySelect, TaskStatus] = {
    StrategySelect.ARCHIVE: TaskStatus.TASK_MISS,
    StrategySelect.MODIFY: TaskStatus.PENDING,
    StrategySelect.KEEP: TaskStatus.TASK_MISS,
}


class TaskStrategyServiceImpl:
    """전략 선택 처리 구현체."""

    def apply_strategy(self, task_id: int, request: ApplyStrategyRequest) -> ApplyStrategyResponse:
        start_ns = time.perf_counter_ns()
        now = datetime.now(timezone.utc)
        session_factory = get_session_factory()

        with session_factory() as session:
            task: Task | None = session.get(Task, task_id)
            if task is None:
                raise ValueError(f"과업을 찾을 수 없습니다: task_id={task_id}")

            previous_status = task.status.value if isinstance(task.status, TaskStatus) else str(task.status)
            new_status = _STRATEGY_STATUS_MAP[request.strategy_select]

            task.status = new_status
            task.updated_at = now

            if request.strategy_select == StrategySelect.ARCHIVE:
                task.is_archived = True

            if request.strategy_select == StrategySelect.MODIFY and request.new_due_date:
                task.due_date = request.new_due_date
                task.is_archived = False

            if request.strategy_select == StrategySelect.KEEP:
                task.is_archived = False

            session.commit()
            session.refresh(task)

            is_archived = task.is_archived
            current_status = task.status.value if isinstance(task.status, TaskStatus) else str(task.status)
            user_id = task.user_id

        self._invalidate_miss_cache(user_id)

        elapsed_ms = (time.perf_counter_ns() - start_ns) / 1_000_000
        logger.info(
            "[%s][PRO-B-21] 전략 적용 task=%d strategy=%s %s→%s archived=%s (%.3fms)",
            now.isoformat(timespec="milliseconds"),
            task_id,
            request.strategy_select.value,
            previous_status,
            current_status,
            is_archived,
            elapsed_ms,
        )

        return ApplyStrategyResponse(
            task_id=task_id,
            previous_status=previous_status,
            current_status=current_status,
            strategy_applied=request.strategy_select,
            is_archived=is_archived,
            timestamp=now,
        )

    def get_active_tasks(self, user_id: str) -> list[Task]:
        """is_archived=False인 과업만 반환하여 보관 과업을 활성 리스트에서 제외한다."""
        session_factory = get_session_factory()
        with session_factory() as session:
            tasks = (
                session.query(Task)
                .filter(and_(Task.user_id == user_id, Task.is_archived == False))  # noqa: E712
                .order_by(Task.due_date.asc())
                .all()
            )
            session.expunge_all()
        return tasks

    @staticmethod
    def _invalidate_miss_cache(user_id: str) -> None:
        client = get_redis()
        if client is None:
            return
        try:
            client.delete(REDIS_MISS_KEY.format(user_id=user_id))
        except Exception:
            logger.warning("[PRO-B-21] Redis 캐시 무효화 실패 user=%s", user_id, exc_info=True)
