"""
Github APP JWT 생성
"""
import time
from datetime import datetime, timedelta

import jwt
from loguru import logger

def generate_jwt(app_id: str, private_key: bytes, expiration_seconds: int = 600) -> str:
    """
    Github APP authentication을 위한 JWT 토큰 생성

    Args:
        app_id (str): Github APP ID
        private_key (bytes): Github APP private key
        expiration_seconds (int, optional): JWT 토큰의 만료 시간. Defaults to 600.

    Returns:
        str: JWT 토큰
    
    Raises:
        ValueError: expiration_seconds > 600 (Github API의 제한)
    """
    if expiration_seconds > 600:
        raise ValueError("Github APP JWT 토큰이 만료 시간(10분)을 초과할 수 없습니다.")
    
    now = int(time.time())

    # JWT payload 생성
    payload = {
        "iat": now - 60,
        "exp": now + expiration_seconds,
        "iss": app_id
    }

    # RS256 알고리듬을 이용해 JWT 토큰 생성
    token = jwt.encode(
        payload,
        private_key,
        algorithm="RS256"
    )

    logger.debug(f"Generated JWT token: {token}, app_id: {app_id}, expiration_seconds: {expiration_seconds}")

    return token