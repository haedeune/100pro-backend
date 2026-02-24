"""
TriggerSettings 싱글톤 [PRO-B-25].
ParameterRegistry를 래핑하여 PRO-B-25 파라미터에 대한
타입 안전 접근과 실시간 반영을 보장한다.
외부 설정값 변경만으로 로직 수정 없이 실험·운영 변수를 제어할 수 있다.
"""
from app.infrastructure.task_params.registry import ParameterRegistry


class TriggerSettings:
    """
    [PRO-B-25] 실험 트리거·운영 변수 싱글톤 접근자.
    모든 값은 DB system_parameters에서 실시간으로 읽으므로
    코드 배포 없이 파라미터 조작만으로 제어 가능하다.
    """

    @staticmethod
    def trigger_miss_threshold() -> int:
        """[PRO-B-25] 팝업 트리거 누적 실패 임계치."""
        return ParameterRegistry().get("TRIGGER_MISS_THRESHOLD", 1)

    @staticmethod
    def available_strategy_options() -> list[str]:
        """[PRO-B-25] 유저에게 제공할 관리 옵션 배열."""
        return ParameterRegistry().get("AVAILABLE_STRATEGY_OPTIONS", ["Archive", "Modify", "Keep"])

    @staticmethod
    def post_miss_exit_window() -> int:
        """[PRO-B-25] 실패 후 이탈 판정 기준 시간 (초)."""
        return ParameterRegistry().get("POST_MISS_EXIT_WINDOW", 60)

    @staticmethod
    def max_archive_limit() -> int:
        """[PRO-B-25] 사용자별 보관함 최대 적재 수량."""
        return ParameterRegistry().get("MAX_ARCHIVE_LIMIT", 20)

    @staticmethod
    def exp_b10_ratio() -> float:
        """[PRO-B-25] B10 실험군/대조군 할당 비율 (0.0‒1.0)."""
        return ParameterRegistry().get("EXP_PROB_B10_RATIO", 0.5)

    @staticmethod
    def as_dict() -> dict:
        """[PRO-B-25] 전체 트리거·운영 설정을 딕셔너리로 반환한다."""
        return {
            "TRIGGER_MISS_THRESHOLD": TriggerSettings.trigger_miss_threshold(),
            "AVAILABLE_STRATEGY_OPTIONS": TriggerSettings.available_strategy_options(),
            "POST_MISS_EXIT_WINDOW": TriggerSettings.post_miss_exit_window(),
            "MAX_ARCHIVE_LIMIT": TriggerSettings.max_archive_limit(),
            "EXP_PROB_B10_RATIO": TriggerSettings.exp_b10_ratio(),
        }

    @staticmethod
    def refresh() -> int:
        """[PRO-B-25] 캐시를 강제 갱신한다."""
        return ParameterRegistry().force_refresh()
