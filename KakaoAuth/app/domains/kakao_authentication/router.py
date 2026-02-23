"""
Kakao 인증 API 라우터.
Service 인터페이스에만 의존하며, 요청 전달 및 응답 반환만 수행한다.
"""
from fastapi import APIRouter, HTTPException, Query

from app.domains.kakao_authentication.exceptions import (
    KakaoOAuthConfigError,
    KakaoTokenError,
    KakaoUserInfoError,
)
from app.domains.kakao_authentication.schemas import OAuthLinkResponse, TokenAndUserResponse
from app.domains.kakao_authentication.service import KakaoAuthenticationServiceImpl

router = APIRouter()
_service: KakaoAuthenticationServiceImpl | None = None


def get_service() -> KakaoAuthenticationServiceImpl:
    """Service 구현체 싱글톤 반환 (Controller는 인터페이스 타입으로만 사용)."""
    global _service
    if _service is None:
        _service = KakaoAuthenticationServiceImpl()
    return _service


@router.get("/request-oauth-link", response_model=OAuthLinkResponse)
def request_oauth_link() -> OAuthLinkResponse:
    """Kakao OAuth 인증 URL을 반환한다. 사용자는 해당 URL로 이동해 인증 후 리다이렉트된다."""
    service = get_service()
    try:
        return service.get_oauth_link()
    except KakaoOAuthConfigError as e:
        raise HTTPException(status_code=500, detail=e.detail or e.message)


@router.get("/request-access-token-after-redirection", response_model=TokenAndUserResponse)
def request_access_token_after_redirection(
    code: str = Query(..., description="Kakao 인증 후 리다이렉트된 인가 코드"),
) -> TokenAndUserResponse:
    """인가 코드로 액세스 토큰을 발급하고, 해당 토큰으로 사용자 정보를 조회하여 반환한다."""
    service = get_service()
    try:
        return service.request_access_token_after_redirection(code)
    except KakaoOAuthConfigError as e:
        raise HTTPException(status_code=500, detail=e.detail or e.message)
    except KakaoTokenError as e:
        raise HTTPException(status_code=400, detail=e.detail or e.message)
    except KakaoUserInfoError as e:
        raise HTTPException(status_code=401, detail=e.detail or e.message)
