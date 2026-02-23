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

    from app.infrastructure.task_params.defaults import seed_defaults
    from app.infrastructure.experiment_config.defaults import seed_experiment_config
    from app.core.database import get_session_factory
    with get_session_factory()() as session:
        seed_defaults(session)
        seed_experiment_config(session)

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
from app.infrastructure.task_archive import router as task_archive_router  # noqa: E402
from app.infrastructure.task_tracking import router as task_tracking_router  # noqa: E402
from app.infrastructure.task_params import router as task_params_router  # noqa: E402
from app.infrastructure.experiment_config import router as experiment_config_router  # noqa: E402

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

app.include_router(
    task_archive_router,
    prefix="/task-archive",
    tags=["task-archive [PRO-B-23]"],
)

app.include_router(
    task_tracking_router,
    prefix="/task-tracking",
    tags=["task-tracking [PRO-B-24]"],
)

app.include_router(
    task_params_router,
    prefix="/params",
    tags=["params [PRO-B-16]"],
)

app.include_router(
    experiment_config_router,
    prefix="/experiment-config",
    tags=["experiment-config [PRO-B-22]"],
)
