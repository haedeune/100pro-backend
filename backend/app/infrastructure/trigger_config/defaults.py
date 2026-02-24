"""
PRO-B-25 전용 파라미터 기본값 정의 및 시드 함수 [PRO-B-25].
기존 system_parameters 테이블에 삽입한다.
이미 PRO-B-22에서 등록된 키는 건너뛰고, 신규 키(EXP_PROB_B10_RATIO)만 추가한다.
"""
import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.infrastructure.task_params.defaults import ParamDefault
from app.infrastructure.task_params.models import SystemParameter

logger = logging.getLogger(__name__)

# [PRO-B-25] 실험 트리거 임계치 및 운영 제어 변수
TRIGGER_CONFIG_DEFAULTS: list[ParamDefault] = [
    ParamDefault(
        key="TRIGGER_MISS_THRESHOLD",
        value="1",
        value_type="int",
        category="experiment",
        description="[PRO-B-25] 팝업 트리거를 위한 누적 실패 과업 수 임계치 (Default: 1)",
    ),
    ParamDefault(
        key="AVAILABLE_STRATEGY_OPTIONS",
        value='["Archive", "Modify", "Keep"]',
        value_type="json",
        category="policy",
        description='[PRO-B-25] 유저 제공 관리 옵션 배열 (Default: ["Archive", "Modify", "Keep"])',
    ),
    ParamDefault(
        key="POST_MISS_EXIT_WINDOW",
        value="60",
        value_type="int",
        category="threshold",
        description="[PRO-B-25] 실패 후 이탈 판정 기준 시간 (초, Default: 60)",
    ),
    ParamDefault(
        key="MAX_ARCHIVE_LIMIT",
        value="20",
        value_type="int",
        category="policy",
        description="[PRO-B-25] 사용자별 보관함 최대 적재 수량 (Default: 20)",
    ),
    ParamDefault(
        key="EXP_PROB_B10_RATIO",
        value="0.5",
        value_type="float",
        category="experiment",
        description="[PRO-B-25] B10 실험군/대조군 무작위 할당 비율 (0.0‒1.0, Default: 0.5)",
    ),
]


def seed_trigger_config(session: Session) -> int:
    """
    [PRO-B-25] DB에 존재하지 않는 파라미터를 기본값으로 삽입한다.
    이미 존재하는 키는 건너뛴다 (운영 중 변경된 값 보호).
    """
    now = datetime.now(timezone.utc)
    existing_keys: set[str] = {
        row[0] for row in session.query(SystemParameter.key).all()
    }

    inserted = 0
    for param in TRIGGER_CONFIG_DEFAULTS:
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
        logger.info("[PRO-B-25] 트리거 설정 시드 완료: %d건 삽입", inserted)
    else:
        logger.info("[PRO-B-25] 트리거 설정 시드: 신규 항목 없음")

    return inserted
