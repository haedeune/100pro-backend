"""
Kakao 인증 Service 구현체.
환경 변수(.env) 기반으로 client_id, redirect_uri를 로드하며, URL/토큰/사용자정보 로직을 담당한다.
"""
import os
from urllib.parse import urlencode

import httpx

from app.domains.kakao_authentication.exceptions import (
    KakaoOAuthConfigError,
    KakaoTokenError,
    KakaoUserInfoError,
)
from app.domains.kakao_authentication.schemas import (
    KakaoUserInfo,
    OAuthLinkResponse,
    TokenAndUserResponse,
)

KAKAO_AUTH_BASE = "https://kauth.kakao.com"
KAKAO_API_BASE = "https://kapi.kakao.com"


class KakaoAuthenticationServiceImpl:
    """Kakao OAuth 인증 URL 생성, 토큰 발급, 사용자 정보 조회 구현체."""

    def __init__(
        self,
        client_id: str | None = None,
        redirect_uri: str | None = None,
        client_secret: str | None = None,
    ) -> None:
        self._client_id = client_id or os.getenv("KAKAO_CLIENT_ID")
        self._redirect_uri = redirect_uri or os.getenv("KAKAO_REDIRECT_URI")
        self._client_secret = client_secret or os.getenv("KAKAO_CLIENT_SECRET")

    def get_oauth_link(self) -> OAuthLinkResponse:
        """Kakao OAuth 인증 URL을 생성하여 반환한다."""
        if not self._client_id or not self._redirect_uri:
            raise KakaoOAuthConfigError(
                "Kakao OAuth 설정이 누락되었습니다.",
                detail="KAKAO_CLIENT_ID, KAKAO_REDIRECT_URI 환경 변수를 확인하세요.",
            )
        params = {
            "response_type": "code",
            "client_id": self._client_id,
            "redirect_uri": self._redirect_uri,
        }
        url = f"{KAKAO_AUTH_BASE}/oauth/authorize?{urlencode(params)}"
        return OAuthLinkResponse(oauth_link=url)

    def request_access_token_after_redirection(self, code: str) -> TokenAndUserResponse:
        """인가 코드로 액세스 토큰을 발급하고, 사용자 정보를 조회하여 반환한다 (PM-JSH-3 + PM-JSH-4)."""
        if not code or not code.strip():
            raise KakaoTokenError("인가 코드(code)가 필요합니다.", detail="code 파라미터를 전달하세요.")
        if not self._client_id or not self._redirect_uri:
            raise KakaoOAuthConfigError(
                "Kakao OAuth 설정이 누락되었습니다.",
                detail="KAKAO_CLIENT_ID, KAKAO_REDIRECT_URI 환경 변수를 확인하세요.",
            )

        token_data = self._request_token(code)
        user_info = self._fetch_user_info(token_data["access_token"])
        return TokenAndUserResponse(
            access_token=token_data["access_token"],
            token_type=token_data.get("token_type", "bearer"),
            expires_in=token_data["expires_in"],
            refresh_token=token_data["refresh_token"],
            refresh_token_expires_in=token_data["refresh_token_expires_in"],
            user=user_info,
        )

    def _request_token(self, code: str) -> dict:
        """Kakao 토큰 서버에 토큰 요청."""
        payload = {
            "grant_type": "authorization_code",
            "client_id": self._client_id,
            "redirect_uri": self._redirect_uri,
            "code": code.strip(),
        }
        if self._client_secret:
            payload["client_secret"] = self._client_secret

        with httpx.Client() as client:
            resp = client.post(
                f"{KAKAO_AUTH_BASE}/oauth/token",
                data=payload,
                headers={"Content-Type": "application/x-www-form-urlencoded;charset=utf-8"},
            )
        if resp.status_code != 200:
            body = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
            error_msg = body.get("error_description", body.get("error", resp.text)) or "토큰 발급에 실패했습니다."
            raise KakaoTokenError(error_msg, detail=str(body))
        data = resp.json()
        for key in ("access_token", "expires_in", "refresh_token", "refresh_token_expires_in"):
            if key not in data:
                raise KakaoTokenError(f"토큰 응답에 필수 필드가 없습니다: {key}")
        return data

    def _fetch_user_info(self, access_token: str) -> KakaoUserInfo:
        """액세스 토큰으로 Kakao 사용자 정보 조회 (PM-JSH-4)."""
        with httpx.Client() as client:
            resp = client.get(
                f"{KAKAO_API_BASE}/v2/user/me",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/x-www-form-urlencoded;charset=utf-8",
                },
            )
        if resp.status_code != 200:
            body = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
            error_msg = body.get("msg", body.get("error_description", "사용자 정보 조회에 실패했습니다."))
            raise KakaoUserInfoError(error_msg, detail=str(body))
        data = resp.json()
        kakao_account = data.get("kakao_account") or {}
        profile = kakao_account.get("profile") or {}
        return KakaoUserInfo(
            id=data.get("id", 0),
            nickname=profile.get("nickname"),
            email=kakao_account.get("email"),
        )
