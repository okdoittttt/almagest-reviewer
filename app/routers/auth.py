"""GitHub OAuth 로그인 라우터."""
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import RedirectResponse

from app.auth.user_jwt import create_user_token
from app.config import settings
from app.dependencies.auth import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])

_GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
_GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
_GITHUB_USER_URL = "https://api.github.com/user"

_COOKIE_NAME = "almagest_token"
_COOKIE_MAX_AGE = settings.jwt_expire_hours * 3600


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
    """GitHub OAuth 콜백 — 코드를 httpOnly 쿠키로 교환 후 프론트로 리다이렉트합니다."""
    async with httpx.AsyncClient() as client:
        # 1. code → access_token 교환 (서버 간 통신, client_secret 클라이언트에 미노출)
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

    # 4. JWT를 httpOnly 쿠키에 저장 후 대시보드로 리다이렉트
    #    URL에 토큰을 노출하지 않으므로 브라우저 히스토리/로그에 남지 않음
    jwt_token = create_user_token(github_login)
    response = RedirectResponse("/", status_code=302)
    response.set_cookie(
        key=_COOKIE_NAME,
        value=jwt_token,
        httponly=True,    # JS에서 접근 불가 (XSS 방어)
        samesite="lax",   # CSRF 방어
        max_age=_COOKIE_MAX_AGE,
        path="/",
    )
    return response


@router.get("/me")
async def me(current_user: dict = Depends(get_current_user)) -> dict:
    """현재 로그인된 사용자 정보를 반환합니다."""
    return {"login": current_user["sub"]}


@router.post("/logout")
async def logout(response: Response) -> dict:
    """로그아웃 — httpOnly 쿠키를 삭제합니다."""
    response.delete_cookie(key=_COOKIE_NAME, path="/")
    return {"detail": "로그아웃 되었습니다."}
