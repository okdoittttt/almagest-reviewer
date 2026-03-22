"""인증 의존성 — API 라우터에서 Depends(get_current_user)로 사용."""
import jwt
from fastapi import Cookie, HTTPException, status

from app.auth.user_jwt import verify_user_token


async def get_current_user(
    almagest_token: str | None = Cookie(None),
) -> dict:
    """httpOnly 쿠키에서 JWT를 읽어 검증하고 payload를 반환합니다.

    Returns:
        dict: {"sub": github_login}

    Raises:
        HTTPException: 쿠키가 없거나 토큰이 유효하지 않은 경우 401.
    """
    if almagest_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="인증이 필요합니다.",
        )
    try:
        return verify_user_token(almagest_token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="토큰이 만료되었습니다.",
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 토큰입니다.",
        )
