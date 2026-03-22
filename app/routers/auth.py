"""GitHub OAuth 로그인 라우터."""
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse

from app.auth.user_jwt import create_user_token
from app.config import settings
from app.dependencies.auth import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])

_GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
_GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
_GITHUB_USER_URL = "https://api.github.com/user"


@router.get("/login")
async def login() -> RedirectResponse:
    """GitHub OAuth 인증 화면으로 리다이렉트합니다."""
    if not settings.github_client_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GITHUB_CLIENT_ID가 설정되지 않았습니다.",
        )
    params = urlencode({
        "client_id": settings.github_client_id,
        "scope": "read:user",
    })
    return RedirectResponse(f"{_GITHUB_AUTHORIZE_URL}?{params}")


@router.get("/callback")
async def callback(code: str) -> RedirectResponse:
    """GitHub OAuth 콜백 — 코드를 JWT로 교환 후 프론트로 리다이렉트합니다."""
    async with httpx.AsyncClient() as client:
        # 1. code → access_token 교환
        token_res = await client.post(
            _GITHUB_TOKEN_URL,
            json={
                "client_id": settings.github_client_id,
                "client_secret": settings.github_client_secret,
                "code": code,
            },
            headers={"Accept": "application/json"},
        )
        token_data = token_res.json()
        access_token = token_data.get("access_token")
        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="GitHub에서 access_token을 받지 못했습니다.",
            )

        # 2. access_token → GitHub 사용자 정보 조회
        user_res = await client.get(
            _GITHUB_USER_URL,
            headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
        )
        user_data = user_res.json()
        github_login = user_data.get("login", "")

    # 3. 허용 목록 확인
    allowed = [u.strip() for u in settings.allowed_github_users.split(",") if u.strip()]
    if allowed and github_login not in allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"'{github_login}' 계정은 접근 권한이 없습니다.",
        )

    # 4. JWT 발급 후 프론트엔드로 리다이렉트
    jwt_token = create_user_token(github_login)
    return RedirectResponse(f"/?token={jwt_token}")


@router.get("/me")
async def me(current_user: dict = Depends(get_current_user)) -> dict:
    """현재 로그인된 사용자 정보를 반환합니다."""
    return {"login": current_user["sub"]}


@router.post("/logout")
async def logout() -> dict:
    """로그아웃 — 클라이언트 측 토큰 삭제를 안내합니다."""
    return {"detail": "로그아웃 되었습니다."}
