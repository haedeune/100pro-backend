"""
TodayFocus 설정 [PM-TF-PAR-01].
TaskDisplayScope 등 표시 범위 파라미터를 ParameterRegistry로 읽는다.
기본값 today(당일 기준 할일만 표시).
"""
from app.infrastructure.task_params.registry import ParameterRegistry


class TodayFocusSettings:
    """[PM-TF-PAR-01] 홈 화면 할 일 표시 범위 등 TodayFocus 설정."""

    @staticmethod
    def task_display_scope() -> str:
        """[PM-TF-PAR-01] TaskDisplayScope 설정값. 기본값: today."""
        return ParameterRegistry().get("TASK_DISPLAY_SCOPE", "today")
