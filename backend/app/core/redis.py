"""
Redis 클라이언트 싱글톤.
REDIS_URL 환경 변수가 없으면 localhost:6379/0 을 기본값으로 사용한다.
Redis 연결 실패 시에도 애플리케이션은 정상 구동되며, 캐시 미스로 처리된다.
"""
import logging
import os

import redis

logger = logging.getLogger(__name__)

_client: redis.Redis | None = None
_available: bool = False


def get_redis() -> redis.Redis | None:
    """Redis 클라이언트를 반환한다. 연결 불가 시 None."""
    global _client, _available
    if _client is None:
        url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        try:
            _client = redis.from_url(url, decode_responses=True, socket_connect_timeout=2)
            _client.ping()
            _available = True
            logger.info("Redis 연결 성공: %s", url)
        except Exception:
            logger.warning("Redis 연결 실패 — 캐시 없이 동작합니다.")
            _client = None
            _available = False
    return _client if _available else None


def close_redis() -> None:
    """Redis 연결을 종료한다."""
    global _client, _available
    if _client is not None:
        try:
            _client.close()
        except Exception:
            pass
        _client = None
        _available = False
