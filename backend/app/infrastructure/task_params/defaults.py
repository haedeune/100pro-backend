"""
파라미터 기본값 정의 및 시드 함수 [PRO-B-16].
앱 시작 시 DB에 없는 파라미터를 기본값으로 삽입한다.
"""
import logging
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.infrastructure.task_params.models import SystemParameter

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ParamDefault:
    """파라미터 기본값 정의."""

    key: str
    value: str
    value_type: str
    category: str
    description: str


# [PRO-B-16] 전체 파라미터 기본값 정의
PARAM_DEFAULTS: list[ParamDefault] = [
    # ── 1. 실험 환경 제어 ──
    ParamDefault(
        key="EXP_PROB_B1_RATIO",
        value="0.5",
        value_type="float",
        category="experiment",
        description="실험군/대조군 분할 비율 (0.0‒1.0, Default: 0.5 = 5:5)",
    ),
    ParamDefault(
        key="EXP_PROB_B1_ACTIVE",
        value="true",
        value_type="bool",
        category="experiment",
        description="실험 활성화 플래그 (true/false)",
    ),
    # ── 2. 시간 및 행동 임계치 ──
    ParamDefault(
        key="MISS_DETECTION_GRACE_PERIOD",
        value="0",
        value_type="int",
        category="threshold",
        description="마감 후 실패 확정까지 유예 시간 (초, Default: 0)",
    ),
    ParamDefault(
        key="STRATEGY_POPUP_DELAY",
        value="0",
        value_type="int",
        category="threshold",
        description="실패 감지 후 전략 선택 팝업 노출 대기 시간 (초, Default: 0)",
    ),
    ParamDefault(
        key="EXIT_WINDOW_THRESHOLD",
        value="60",
        value_type="int",
        category="threshold",
        description="실패 후 이탈(PostMissExit) 판정 기준 시간 (초, Default: 60)",
    ),
    # ── 3. 운영 및 정책 ──
    ParamDefault(
        key="MAX_ARCHIVE_COUNT",
        value="20",
        value_type="int",
        category="policy",
        description="유저 1인당 보관함 최대 과업 수 (Default: 20)",
    ),
    ParamDefault(
        key="RECOVERY_VALID_DAYS",
        value="7",
        value_type="int",
        category="policy",
        description="보관 후 복구(성공) 인정 최대 기간 (일, Default: 7)",
    ),
    ParamDefault(
        key="RE_ENGAGE_REMIND_INTERVAL",
        value="3",
        value_type="int",
        category="policy",
        description="보관함 과업 재참여 유도 알림 주기 (일, Default: 3)",
    ),
    # ── 4. TodayFocus (PM-TF-PAR-01) ──
    ParamDefault(
        key="TASK_DISPLAY_SCOPE",
        value="today",
        value_type="str",
        category="today_focus",
        description="[PM-TF-PAR-01] 홈 화면 할 일 표시 범위 (today: 당일 기준만, 기본값: today)",
    ),
]


def seed_defaults(session: Session) -> int:
    """
    DB에 존재하지 않는 파라미터를 기본값으로 삽입한다.
    이미 존재하는 키는 건너뛴다 (운영 중 변경된 값 보호).
    삽입된 파라미터 수를 반환한다.
    """
    now = datetime.now(timezone.utc)
    existing_keys: set[str] = {
        row[0]
        for row in session.query(SystemParameter.key).all()
    }

    inserted = 0
    for param in PARAM_DEFAULTS:
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
        logger.info("[PRO-B-16] 파라미터 시드 완료: %d건 삽입", inserted)
    else:
        logger.info("[PRO-B-16] 파라미터 시드: 신규 항목 없음")

    return inserted
