"""Kakao 인증 도메인 예외."""


class KakaoAuthenticationError(Exception):
    """Kakao 인증 관련 기본 예외."""

    def __init__(self, message: str, detail: str | None = None) -> None:
        self.message = message
        self.detail = detail
        super().__init__(message)


class KakaoOAuthConfigError(KakaoAuthenticationError):
    """필수 OAuth 설정(client_id, redirect_uri) 누락 등."""


class KakaoTokenError(KakaoAuthenticationError):
    """토큰 발급 실패(잘못된 코드, 파라미터 누락 등)."""


class KakaoUserInfoError(KakaoAuthenticationError):
    """사용자 정보 조회 실패(유효하지 않은/만료된 토큰 등)."""
