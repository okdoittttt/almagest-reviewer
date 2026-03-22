"""사용자 인증용 JWT 생성 및 검증."""
from datetime import datetime, timedelta, timezone

import jwt

from app.config import settings


def create_user_token(github_login: str) -> str:
    payload = {
        "sub": github_login,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(hours=settings.jwt_expire_hours),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def verify_user_token(token: str) -> dict:
    """토큰 검증 후 payload 반환. 실패 시 예외 발생."""
    return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
