"""
실험 분기 설정값 [PRO-B-21].
환경 변수로 오버라이드 가능하며, 미설정 시 기본값을 사용한다.
"""
import os

DEFAULT_TRIGGER_MISS_THRESHOLD = 3
DEFAULT_FEATURE_FLAG_ENABLED = True
DEFAULT_EXPERIMENT_RATIO = 50  # 실험군 비율 (0‒100)


def get_trigger_miss_threshold() -> int:
    return int(os.getenv("TRIGGER_MISS_THRESHOLD", str(DEFAULT_TRIGGER_MISS_THRESHOLD)))


def is_feature_flag_enabled() -> bool:
    val = os.getenv("FEATURE_FLAG_EXPERIMENT_ENABLED", str(DEFAULT_FEATURE_FLAG_ENABLED))
    return val.lower() in ("true", "1", "yes")


def get_experiment_ratio() -> int:
    """실험군 할당 비율(0‒100). 해시값 % 100 이 이 값 미만이면 실험군."""
    return int(os.getenv("EXPERIMENT_RATIO", str(DEFAULT_EXPERIMENT_RATIO)))
