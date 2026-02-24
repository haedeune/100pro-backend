"""
Kakao 인증 Service 인터페이스.
Controller는 이 인터페이스에만 의존하며, 구현체에 직접 의존하지 않는다.
"""
from typing import Protocol

from app.domains.kakao_authentication.schemas import OAuthLinkResponse, TokenAndUserResponse


class KakaoAuthenticationService(Protocol):
    """Kakao OAuth 인증 URL 생성, 토큰 발급, 사용자 정보 조회 서비스 인터페이스."""

    def get_oauth_link(self) -> OAuthLinkResponse:
        """Kakao OAuth 인증 URL을 생성하여 반환한다."""
        ...

    def request_access_token_after_redirection(self, code: str) -> TokenAndUserResponse:
        """인가 코드로 액세스 토큰을 발급하고, 발급된 토큰으로 사용자 정보를 조회하여 반환한다."""
        ...
