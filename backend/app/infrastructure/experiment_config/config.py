"""
타입 안전 실험 설정 접근자 [PRO-B-22].
ParameterRegistry를 래핑하여 PRO-B-22 파라미터에 대한
명시적 메서드와 타입 힌트를 제공한다.
코드 내에서 registry.get("KEY") 대신 ExperimentConfig.trigger_miss_threshold() 로 호출 가능.
"""
from app.infrastructure.task_params.registry import ParameterRegistry


class ExperimentConfig:
    """
    [PRO-B-22] 실험·운영 파라미터 타입 안전 접근자.
    모든 값은 ParameterRegistry(DB + 캐시)에서 실시간으로 읽으므로
    코드 배포 없이 변경이 반영된다.
    """

    @staticmethod
    def trigger_miss_threshold() -> int:
        """팝업 트리거를 위한 누적 미완료 과업 수 임계치."""
        return ParameterRegistry().get("TRIGGER_MISS_THRESHOLD", 1)

    @staticmethod
    def available_strategy_options() -> list[str]:
        """유저에게 제공할 관리 옵션 배열."""
        return ParameterRegistry().get("AVAILABLE_STRATEGY_OPTIONS", ["Archive", "Modify", "Keep"])

    @staticmethod
    def post_miss_exit_window() -> int:
        """실패 이벤트 후 이탈 판정 최대 허용 시간 (초)."""
        return ParameterRegistry().get("POST_MISS_EXIT_WINDOW", 60)

    @staticmethod
    def max_archive_limit() -> int:
        """사용자별 보관함 최대 레코드 수."""
        return ParameterRegistry().get("MAX_ARCHIVE_LIMIT", 20)

    @staticmethod
    def exp_ratio() -> float:
        """실험군/대조군 할당 비율 (0.0‒1.0)."""
        return ParameterRegistry().get("EXP_PROB_B1_RATIO", 0.5)

    @staticmethod
    def is_experiment_active() -> bool:
        """실험 활성화 여부."""
        return ParameterRegistry().get("EXP_PROB_B1_ACTIVE", True)

    @staticmethod
    def as_dict() -> dict:
        """[PRO-B-22] 전체 실험·운영 설정을 딕셔너리로 반환한다."""
        return {
            "TRIGGER_MISS_THRESHOLD": ExperimentConfig.trigger_miss_threshold(),
            "AVAILABLE_STRATEGY_OPTIONS": ExperimentConfig.available_strategy_options(),
            "POST_MISS_EXIT_WINDOW": ExperimentConfig.post_miss_exit_window(),
            "MAX_ARCHIVE_LIMIT": ExperimentConfig.max_archive_limit(),
            "EXP_PROB_B1_RATIO": ExperimentConfig.exp_ratio(),
            "EXP_PROB_B1_ACTIVE": ExperimentConfig.is_experiment_active(),
        }
