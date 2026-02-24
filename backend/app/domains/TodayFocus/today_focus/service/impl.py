"""
TodayFocus Service 구현체 [PM-TF-PAR-01].
TaskDisplayScope 설정을 읽어 Repository에 today 조건을 적용한다.
"""
from app.domains.TodayFocus.today_focus.repository import HomeTaskRepository
from app.domains.TodayFocus.today_focus.service.interface import TodayFocusServiceProtocol
from app.domains.TodayFocus.today_focus.settings import TodayFocusSettings
from app.domains.task.models import Task


class TodayFocusServiceImpl(TodayFocusServiceProtocol):
    """[PM-TF-PAR-01] 홈 화면 할 일 조회 구현체. 정책/쿼리는 Service·Repository에서 처리."""

    def __init__(self) -> None:
        self._repository = HomeTaskRepository()

    def get_home_tasks(self, user_id: str) -> list[Task]:
        """설정된 TaskDisplayScope에 따라 홈에 표시할 과업만 반환. 오늘 할 일 없으면 빈 리스트."""
        scope = TodayFocusSettings.task_display_scope()
        return self._repository.get_tasks_for_home(user_id, scope)
