"""
파라미터 관리 서비스 구현체 [PRO-B-16].
DB CRUD + 레지스트리 캐시 갱신을 함께 처리한다.
"""
import logging
import time
from datetime import datetime, timezone
from typing import Optional

from app.core.database import get_session_factory
from app.infrastructure.task_params.models import SystemParameter
from app.infrastructure.task_params.registry import ParameterRegistry
from app.infrastructure.task_params.schemas import ParameterUpdateRequest

logger = logging.getLogger(__name__)


def _cast_value(raw: str, value_type: str) -> None:
    """타입 검증용. 변환 실패 시 예외를 발생시킨다."""
    if value_type == "int":
        int(raw)
    elif value_type == "float":
        float(raw)
    elif value_type == "bool":
        if raw.lower() not in ("true", "false", "1", "0", "yes", "no"):
            raise ValueError(f"bool 타입에 유효하지 않은 값: {raw}")


class ParameterServiceImpl:
    """파라미터 CRUD 구현체 [PRO-B-16]."""

    def get_all(self) -> list[SystemParameter]:
        session_factory = get_session_factory()
        with session_factory() as session:
            params = session.query(SystemParameter).order_by(SystemParameter.category, SystemParameter.key).all()
            session.expunge_all()
        return params

    def get_by_key(self, key: str) -> Optional[SystemParameter]:
        session_factory = get_session_factory()
        with session_factory() as session:
            param = session.query(SystemParameter).filter(SystemParameter.key == key).first()
            if param:
                session.expunge(param)
        return param

    def get_by_category(self, category: str) -> list[SystemParameter]:
        session_factory = get_session_factory()
        with session_factory() as session:
            params = (
                session.query(SystemParameter)
                .filter(SystemParameter.category == category)
                .order_by(SystemParameter.key)
                .all()
            )
            session.expunge_all()
        return params

    def update(self, key: str, request: ParameterUpdateRequest) -> SystemParameter:
        """
        파라미터 값을 업데이트하고 레지스트리 캐시를 즉시 갱신한다.
        value_type에 맞지 않는 값은 거부한다.
        """
        start_ns = time.perf_counter_ns()
        now = datetime.now(timezone.utc)
        session_factory = get_session_factory()

        with session_factory() as session:
            param = session.query(SystemParameter).filter(SystemParameter.key == key).first()
            if param is None:
                raise ValueError(f"파라미터를 찾을 수 없습니다: key={key}")

            # [PRO-B-16] 타입 검증
            _cast_value(request.value, param.value_type)

            old_value = param.value
            param.value = request.value
            param.updated_at = now
            if request.description is not None:
                param.description = request.description

            session.commit()
            session.refresh(param)
            session.expunge(param)

        # [PRO-B-16] 레지스트리 캐시 즉시 갱신
        registry = ParameterRegistry()
        registry.force_refresh()

        elapsed_ms = (time.perf_counter_ns() - start_ns) / 1_000_000
        logger.info(
            "[%s][PRO-B-16] 파라미터 변경 %s: %s → %s (%.3fms)",
            now.isoformat(timespec="milliseconds"),
            key,
            old_value,
            request.value,
            elapsed_ms,
        )

        return param
