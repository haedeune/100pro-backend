"""
Kakao 인증 API 요청/응답 스키마.
FastAPI response_model 및 도메인 DTO로 사용.
"""
from typing import Optional

from pydantic import BaseModel, Field


class OAuthLinkResponse(BaseModel):
    """OAuth 인증 URL 응답."""

    oauth_link: str = Field(..., description="Kakao OAuth 인증 페이지 URL")


class TokenResponse(BaseModel):
    """액세스/리프레시 토큰 응답."""

    access_token: str = Field(..., description="액세스 토큰")
    token_type: str = Field(default="bearer", description="토큰 타입")
    expires_in: int = Field(..., description="액세스 토큰 만료 시간(초)")
    refresh_token: str = Field(..., description="리프레시 토큰")
    refresh_token_expires_in: int = Field(..., description="리프레시 토큰 만료 시간(초)")


class KakaoUserInfo(BaseModel):
    """Kakao 사용자 정보 (동의 시 포함)."""

    id: int = Field(..., description="Kakao 사용자 ID")
    nickname: Optional[str] = Field(None, description="닉네임")
    email: Optional[str] = Field(None, description="이메일(동의 시)")


class TokenAndUserResponse(BaseModel):
    """토큰 발급 + 사용자 정보 조회 통합 응답 (PM-JSH-3 + PM-JSH-4)."""

    access_token: str = Field(..., description="액세스 토큰")
    token_type: str = Field(default="bearer", description="토큰 타입")
    expires_in: int = Field(..., description="액세스 토큰 만료 시간(초)")
    refresh_token: str = Field(..., description="리프레시 토큰")
    refresh_token_expires_in: int = Field(..., description="리프레시 토큰 만료 시간(초)")
    user: KakaoUserInfo = Field(..., description="Kakao 사용자 정보")
