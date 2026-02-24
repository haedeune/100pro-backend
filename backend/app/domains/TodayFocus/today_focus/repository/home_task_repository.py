"""
TodayFocus 홈 할 일 조회 Repository [PM-TF-PAR-01].
Scope에 따라 당일만 또는 전체 활성 할일을 조회한다.
today 범위는 KST(Asia/Seoul) 기준 오늘 00:00 ~ 다음날 00:00을 UTC로 변환해 반개구간으로 적용한다.
"""
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import and_

from app.core.database import get_session_factory
from app.domains.task.models import Task

KST = ZoneInfo("Asia/Seoul")


def _today_range_utc() -> tuple[datetime, datetime]:
    """
    KST 기준 오늘 00:00 ~ 다음날 00:00을 UTC로 변환하여 반환한다.
    반개구간 [start_utc, end_utc) 에 사용: due_date >= start_utc AND due_date < end_utc.
    """
    now_kst = datetime.now(KST)
    start_kst = now_kst.replace(hour=0, minute=0, second=0, microsecond=0)
    end_kst = start_kst + timedelta(days=1)
    start_utc = start_kst.astimezone(timezone.utc).replace(tzinfo=None)
    end_utc = end_kst.astimezone(timezone.utc).replace(tzinfo=None)
    return start_utc, end_utc


class HomeTaskRepository:
    """홈 화면에 표시할 할일 조회 Repository."""

    def get_tasks_for_home(self, user_id: str, scope: str) -> list[Task]:
        """
        [PM-TF-PAR-01] 표시 범위(scope)에 맞는 활성 할일 목록을 반환한다.
        scope == "today" 이면 due_date가 KST 기준 오늘인 할일만 (반개구간 >= start_utc AND < end_utc),
        그 외에는 is_archived=False 전체. 오늘 할 일이 없으면 빈 리스트 반환.
        """
        session_factory = get_session_factory()
        with session_factory() as session:
            base = session.query(Task).filter(
                and_(Task.user_id == user_id, Task.is_archived == False)  # noqa: E712
            )
            if scope == "today":
                start_utc, end_utc = _today_range_utc()
                base = base.filter(
                    and_(Task.due_date >= start_utc, Task.due_date < end_utc)
                )
            tasks = base.order_by(Task.due_date.asc()).all()
            session.expunge_all()
        return list(tasks)
