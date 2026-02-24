"""
파라미터 레지스트리 싱글톤 [PRO-B-16].
DB의 system_parameters 테이블을 인메모리에 캐싱하고,
TTL 경과 시 자동으로 DB에서 재조회하여 앱 재시작 없이 변경사항을 반영한다.
"""
import logging
import threading
import time
from typing import Any

from app.core.database import get_session_factory
from app.infrastructure.task_params.defaults import PARAM_DEFAULTS
from app.infrastructure.task_params.models import SystemParameter

logger = logging.getLogger(__name__)

CACHE_TTL_SECONDS = 30


def _cast_value(raw: str, value_type: str) -> Any:
    """문자열 값을 지정된 타입으로 변환한다."""
    if value_type == "int":
        return int(raw)
    if value_type == "float":
        return float(raw)
    if value_type == "bool":
        return raw.lower() in ("true", "1", "yes")
    if value_type == "json":  # [PRO-B-22] 배열/객체 타입 지원
        import json
        return json.loads(raw)
    return raw


class ParameterRegistry:
    """
    파라미터 레지스트리 싱글톤 [PRO-B-16].
    get() 호출 시 캐시 TTL이 만료되었으면 DB에서 자동 갱신한다.
    스레드 세이프하게 동작한다.
    """

    _instance: "ParameterRegistry | None" = None
    _lock = threading.Lock()

    def __new__(cls) -> "ParameterRegistry":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    inst = super().__new__(cls)
                    inst._cache: dict[str, tuple[Any, str]] = {}
                    inst._last_refresh: float = 0
                    inst._ttl = CACHE_TTL_SECONDS
                    cls._instance = inst
        return cls._instance

    def get(self, key: str, default: Any = None) -> Any:
        """
        파라미터 값을 반환한다. TTL 만료 시 DB에서 자동 갱신한다.
        조회 우선순위: 인메모리 캐시 → DB → defaults.py → default 인자
        """
        self._refresh_if_stale()
        if key in self._cache:
            return self._cache[key][0]
        fallback = self._get_default(key)
        return fallback if fallback is not None else default

    def get_raw(self, key: str) -> str | None:
        """캐스팅 전 원본 문자열 값을 반환한다."""
        self._refresh_if_stale()
        if key in self._cache:
            return str(self._cache[key][0])
        return None

    def get_all(self) -> dict[str, Any]:
        """모든 파라미터를 {key: value} 딕셔너리로 반환한다."""
        self._refresh_if_stale()
        return {k: v[0] for k, v in self._cache.items()}

    def get_by_category(self, category: str) -> dict[str, Any]:
        """특정 카테고리의 파라미터만 반환한다."""
        self._refresh_if_stale()
        return {k: v[0] for k, v in self._cache.items() if v[1] == category}

    def force_refresh(self) -> int:
        """캐시를 즉시 DB에서 갱신한다. 갱신된 파라미터 수를 반환한다."""
        return self._load_from_db()

    def _refresh_if_stale(self) -> None:
        now = time.monotonic()
        if now - self._last_refresh > self._ttl:
            self._load_from_db()

    def _load_from_db(self) -> int:
        try:
            session_factory = get_session_factory()
            with session_factory() as session:
                rows = session.query(SystemParameter).all()
                new_cache: dict[str, tuple[Any, str]] = {}
                for row in rows:
                    typed_value = _cast_value(row.value, row.value_type)
                    new_cache[row.key] = (typed_value, row.category)
                self._cache = new_cache
                self._last_refresh = time.monotonic()
                logger.debug("[PRO-B-16] 파라미터 캐시 갱신: %d건", len(new_cache))
                return len(new_cache)
        except Exception:
            logger.warning("[PRO-B-16] 파라미터 캐시 갱신 실패", exc_info=True)
            return 0

    @staticmethod
    def _get_default(key: str) -> Any:
        for param in PARAM_DEFAULTS:
            if param.key == key:
                return _cast_value(param.value, param.value_type)
        return None
