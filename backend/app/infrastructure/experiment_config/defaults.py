"""
PRO-B-22 전용 파라미터 기본값 정의 및 시드 함수 [PRO-B-22].
기존 task_params의 시드 메커니즘을 재활용하여 system_parameters 테이블에 삽입한다.
"""
import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.infrastructure.task_params.defaults import ParamDefault
from app.infrastructure.task_params.models import SystemParameter

logger = logging.getLogger(__name__)

# [PRO-B-22] 실험 트리거 임계치 및 운영 변수
EXPERIMENT_CONFIG_DEFAULTS: list[ParamDefault] = [
    ParamDefault(
        key="TRIGGER_MISS_THRESHOLD",
        value="1",
        value_type="int",
        category="experiment",
        description="[PRO-B-22] 팝업 트리거를 위한 누적 미완료 과업 수 임계치 (Default: 1)",
    ),
    ParamDefault(
        key="AVAILABLE_STRATEGY_OPTIONS",
        value='["Archive", "Modify", "Keep"]',
        value_type="json",
        category="policy",
        description='[PRO-B-22] 유저에게 제공할 관리 옵션 배열 (Default: ["Archive", "Modify", "Keep"])',
    ),
    ParamDefault(
        key="POST_MISS_EXIT_WINDOW",
        value="60",
        value_type="int",
        category="threshold",
        description="[PRO-B-22] 실패 이벤트 후 이탈 판정 최대 허용 시간 (초, Default: 60)",
    ),
    ParamDefault(
        key="MAX_ARCHIVE_LIMIT",
        value="20",
        value_type="int",
        category="policy",
        description="[PRO-B-22] 사용자별 보관함 최대 레코드 수 제한 (Default: 20)",
    ),
    ParamDefault(
        key="EXP_PROB_B1_RATIO",
        value="0.5",
        value_type="float",
        category="experiment",
        description="[PRO-B-22] 실험군/대조군 할당 비율 (0.0‒1.0, Default: 0.5)",
    ),
]


def seed_experiment_config(session: Session) -> int:
    """
    [PRO-B-22] DB에 존재하지 않는 실험·운영 파라미터를 기본값으로 삽입한다.
    이미 존재하는 키는 건너뛴다 (운영 중 변경된 값 보호).
    """
    now = datetime.now(timezone.utc)
    existing_keys: set[str] = {
        row[0] for row in session.query(SystemParameter.key).all()
    }

    inserted = 0
    for param in EXPERIMENT_CONFIG_DEFAULTS:
        if param.key in existing_keys:
            continue
        session.add(SystemParameter(
            key=param.key,
            value=param.value,
            value_type=param.value_type,
            category=param.category,
            description=param.description,
            created_at=now,
            updated_at=now,
        ))
        inserted += 1

    if inserted > 0:
        session.commit()
        logger.info("[PRO-B-22] 실험 설정 시드 완료: %d건 삽입", inserted)
    else:
        logger.info("[PRO-B-22] 실험 설정 시드: 신규 항목 없음")

    return inserted
