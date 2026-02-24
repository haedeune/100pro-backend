"""
상태 전환 서비스 구현체 [PRO-B-23].
전략 선택(Archive/Modify/Keep)에 따라 과업 상태를 전환하며,
모든 전환은 TaskStatusHistory에 기록되어 데이터 정합성을 유지한다.
Archive 선택 시 메인 테이블에서 보관함 테이블로 데이터를 격리한다.
"""
import logging
import time
from datetime import datetime, timezone

from app.core.database import get_session_factory
from app.core.redis import get_redis
from app.domains.task.models import Task, TaskStatus
from app.infrastructure.task_archive.models import TaskArchive, TaskStatusHistory
from app.infrastructure.task_archive.repository import ArchiveRepository
from app.infrastructure.task_archive.schemas import StrategyType, TransitionRequest, TransitionResponse

logger = logging.getLogger(__name__)

REDIS_MISS_KEY = "user:{user_id}:miss_count"

# [PRO-B-23] strategy → 전환 대상 상태
_TRANSITION_MAP: dict[StrategyType, TaskStatus] = {
    StrategyType.ARCHIVE: TaskStatus.TASK_MISS,
    StrategyType.MODIFY: TaskStatus.PENDING,
    StrategyType.KEEP: TaskStatus.TASK_MISS,
}


class TaskArchiveServiceImpl:
    """전략 기반 상태 전환 + 보관함 격리 구현체 [PRO-B-23]."""

    def apply_transition(self, task_id: int, request: TransitionRequest) -> TransitionResponse:
        start_ns = time.perf_counter_ns()
        now = datetime.now(timezone.utc)
        session_factory = get_session_factory()
        repo = ArchiveRepository()

        with session_factory() as session:
            task: Task | None = session.get(Task, task_id)
            if task is None:
                raise ValueError(f"과업을 찾을 수 없습니다: task_id={task_id}")

            prev_status = task.status.value if isinstance(task.status, TaskStatus) else str(task.status)
            new_status = _TRANSITION_MAP[request.strategy_select]
            new_status_str = new_status.value
            user_id = task.user_id
            archived = False

            # [PRO-B-23] 상태 변경 이력 기록 (전환 전에 기록하여 Archive 삭제 후에도 보존)
            history = repo.record_history(
                session,
                task_id=task_id,
                previous_status=prev_status,
                new_status="archived" if request.strategy_select == StrategyType.ARCHIVE else new_status_str,
                strategy=request.strategy_select.value,
                now=now,
            )

            if request.strategy_select == StrategyType.ARCHIVE:
                # [PRO-B-23] 보관함 테이블로 격리 (메인 테이블에서 삭제)
                repo.move_to_archive(session, task, now)
                archived = True

            elif request.strategy_select == StrategyType.MODIFY:
                task.status = new_status
                task.updated_at = now
                task.is_archived = False
                if request.new_due_date:
                    task.due_date = request.new_due_date

            elif request.strategy_select == StrategyType.KEEP:
                task.status = new_status
                task.updated_at = now
                task.is_archived = False

            session.flush()
            history_id = history.id
            session.commit()

        self._invalidate_miss_cache(user_id)

        elapsed_ms = (time.perf_counter_ns() - start_ns) / 1_000_000
        logger.info(
            "[%s][PRO-B-23] 전환 완료 task=%d strategy=%s %s→%s archived=%s history=%d (%.3fms)",
            now.isoformat(timespec="milliseconds"),
            task_id,
            request.strategy_select.value,
            prev_status,
            new_status_str if not archived else "archived",
            archived,
            history_id,
            elapsed_ms,
        )

        return TransitionResponse(
            task_id=task_id,
            previous_status=prev_status,
            current_status="archived" if archived else new_status_str,
            strategy_applied=request.strategy_select,
            archived=archived,
            history_id=history_id,
            timestamp=now,
        )

    def get_user_archives(self, user_id: str) -> list[TaskArchive]:
        session_factory = get_session_factory()
        with session_factory() as session:
            archives = ArchiveRepository.get_user_archives(session, user_id)
            session.expunge_all()
        return archives

    def get_task_history(self, task_id: int) -> list[TaskStatusHistory]:
        session_factory = get_session_factory()
        with session_factory() as session:
            history = ArchiveRepository.get_task_history(session, task_id)
            session.expunge_all()
        return history

    @staticmethod
    def _invalidate_miss_cache(user_id: str) -> None:
        client = get_redis()
        if client is None:
            return
        try:
            client.delete(REDIS_MISS_KEY.format(user_id=user_id))
        except Exception:
            logger.warning("[PRO-B-23] Redis 캐시 무효화 실패 user=%s", user_id, exc_info=True)
