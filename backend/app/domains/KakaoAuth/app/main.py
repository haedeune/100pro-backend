"""
FastAPI 애플리케이션 진입점.
시작 시 app.core.env.load_env()를 호출하여 환경 변수를 1회 로드한다.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.domains.KakaoAuth.app.core.env import load_env
##from app.domains.kakao_authentication import router as kakao_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 시작 시 .env 1회 로드."""
    load_env()
    yield


app = FastAPI(
    title="Kakao Authentication API",
    description="PM-JSH Kakao OAuth 인증 API",
    version="1.0.0",
    lifespan=lifespan,
)
##app.include_router(
##    kakao_router,
##    prefix="/kakao-authentication",
##    tags=["kakao-authentication"],
##)
