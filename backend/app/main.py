"""
FastAPI 애플리케이션 진입점.
시작 시 환경 변수 로드, DB 초기화, 스케줄러 시작을 수행한다.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.env import load_env
from app.domains.kakao_authentication import router as kakao_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 시작 시 .env 로드 → DB 초기화 → 스케줄러 시작. 종료 시 스케줄러·Redis 정리."""
    load_env()

    from app.core.database import init_db
    from app.core.redis import close_redis
    from app.infrastructure.task_miss import TaskMissScheduler

    init_db()

    scheduler = TaskMissScheduler()
    scheduler.start()

    yield

    scheduler.shutdown()
    close_redis()


app = FastAPI(
    title="100pro Backend API",
    description="100pro 프로젝트 백엔드 — 과업 관리 및 인프라",
    version="1.1.0",
    lifespan=lifespan,
)

app.include_router(
    kakao_router,
    prefix="/kakao-authentication",
    tags=["kakao-authentication"],
)

from app.infrastructure.task_miss import router as task_miss_router  # noqa: E402
from app.infrastructure.task_strategy import router as task_strategy_router  # noqa: E402

app.include_router(
    task_miss_router,
    prefix="/task-miss",
    tags=["task-miss [PRO-B-10]"],
)

app.include_router(
    task_strategy_router,
    prefix="/task-strategy",
    tags=["task-strategy [PRO-B-21]"],
)
