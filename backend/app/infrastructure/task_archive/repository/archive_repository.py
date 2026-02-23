"""
보관함 리포지토리 [PRO-B-23].
메인 tasks 테이블에서 과업을 삭제하고 task_archives 테이블로 이동(격리)한다.
단일 트랜잭션으로 처리하여 데이터 유실을 방지한다.
"""
import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.domains.task.models import Task, TaskStatus
from app.infrastructure.task_archive.models import TaskArchive, TaskStatusHistory

logger = logging.getLogger(__name__)


class ArchiveRepository:
    """보관함 DB 격리 로직. 단일 세션(트랜잭션) 내에서 호출되어야 한다."""

    @staticmethod
    def move_to_archive(session: Session, task: Task, now: datetime | None = None) -> TaskArchive:
        """
        tasks 레코드를 task_archives로 복사한 뒤 원본을 삭제한다.
        동일 트랜잭션 내에서 수행되므로 caller가 commit을 관리한다.
        """
        now = now or datetime.now(timezone.utc)
        original_status = task.status.value if isinstance(task.status, TaskStatus) else str(task.status)

        archive = TaskArchive(
            original_task_id=task.id,
            title=task.title,
            description=task.description,
            original_status=original_status,
            user_id=task.user_id,
            due_date=task.due_date,
            task_created_at=task.created_at,
            archived_at=now,
        )
        session.add(archive)
        session.delete(task)

        logger.info(
            "[%s][PRO-B-23] 보관함 이동 task_id=%d user=%s",
            now.isoformat(timespec="milliseconds"),
            task.id,
            task.user_id,
        )
        return archive

    @staticmethod
    def record_history(
        session: Session,
        task_id: int,
        previous_status: str,
        new_status: str,
        strategy: str | None = None,
        now: datetime | None = None,
    ) -> TaskStatusHistory:
        """상태 변경 이력을 기록한다. caller가 commit을 관리한다."""
        now = now or datetime.now(timezone.utc)
        history = TaskStatusHistory(
            task_id=task_id,
            previous_status=previous_status,
            new_status=new_status,
            strategy_applied=strategy,
            changed_at=now,
        )
        session.add(history)
        return history

    @staticmethod
    def get_user_archives(session: Session, user_id: str) -> list[TaskArchive]:
        """사용자의 보관함 목록을 반환한다."""
        return (
            session.query(TaskArchive)
            .filter(TaskArchive.user_id == user_id)
            .order_by(TaskArchive.archived_at.desc())
            .all()
        )

    @staticmethod
    def get_task_history(session: Session, task_id: int) -> list[TaskStatusHistory]:
        """특정 과업의 상태 변경 이력을 시간순으로 반환한다."""
        return (
            session.query(TaskStatusHistory)
            .filter(TaskStatusHistory.task_id == task_id)
            .order_by(TaskStatusHistory.changed_at.asc())
            .all()
        )
