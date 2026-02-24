"""TodayFocus Service 인터페이스."""
from app.domains.task.models import Task


class TodayFocusServiceProtocol:
    """홈 화면 할 일 조회 서비스 프로토콜."""

    def get_home_tasks(self, user_id: str) -> list[Task]:
        """TaskDisplayScope에 따라 홈에 표시할 과업 목록을 반환한다."""
        ...
