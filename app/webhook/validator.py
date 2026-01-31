"""
GitHub Webhook 서명 검증
"""
import hmac
import hashlib
import json
from typing import Annotated

from fastapi import Request, HTTPException, Depends
from loguru import logger

from app.config import settings


def calculate_signature(secret: str, payload: bytes) -> str:
    """
    HMAC-SHA256 서명을 계산합니다.

    Args:
        secret: Webhook secret key
        payload: Request body (raw bytes)

    Returns:
        'sha256=' 접두사가 붙은 서명 문자열
    """
    signature = hmac.new(
        secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()

    return f"sha256={signature}"


def verify_signature(signature_header: str, calculated_signature: str) -> bool:
    """
    GitHub에서 보낸 서명과 계산한 서명을 비교합니다.

    타이밍 공격을 방지하기 위해 hmac.compare_digest를 사용합니다.

    Args:
        signature_header: X-Hub-Signature-256 헤더 값
        calculated_signature: 계산한 서명

    Returns:
        서명이 일치하면 True, 아니면 False
    """
    if not signature_header:
        return False

    return hmac.compare_digest(signature_header, calculated_signature)


async def verify_webhook_signature(request: Request) -> bytes:
    """
    GitHub Webhook 서명을 검증하는 FastAPI Dependency 함수

    Request Body의 서명을 검증하고, 검증된 raw bytes를 반환합니다.
    검증 실패 시 HTTPException을 발생시킵니다.

    Args:
        request: FastAPI Request 객체

    Returns:
        검증된 Request Body (raw bytes)

    Raises:
        HTTPException: 서명 검증 실패 시 403 Forbidden
    """
    # 개발 환경에서는 검증 스킵 (선택사항)
    # 프로덕션에서는 반드시 검증해야 합니다
    # if settings.model_extra.get("env") == "development":
    #     logger.warning("개발 환경: Webhook 서명 검증을 스킵합니다")
    #     return await request.body()

    # X-Hub-Signature-256 헤더 추출
    signature_header = request.headers.get("X-Hub-Signature-256")

    if not signature_header:
        logger.error("Webhook 요청에 X-Hub-Signature-256 헤더가 없습니다")
        raise HTTPException(
            status_code=403,
            detail="X-Hub-Signature-256 header is missing"
        )

    # Request Body 읽기 (원본 바이트)
    body = await request.body()

    if not body:
        logger.error("Webhook 요청의 body가 비어있습니다")
        raise HTTPException(
            status_code=400,
            detail="Request body is empty"
        )

    # 서명 계산
    calculated_signature = calculate_signature(settings.github_webhook_secret, body)

    # 서명 검증
    if not verify_signature(signature_header, calculated_signature):
        logger.error(
            f"Webhook 서명 검증 실패 - "
            f"Expected: {calculated_signature[:20]}..., "
            f"Received: {signature_header[:20]}..."
        )
        raise HTTPException(
            status_code=403,
            detail="Invalid webhook signature"
        )

    logger.debug("Webhook 서명 검증 성공")
    return body


# Type alias for dependency
VerifiedWebhookBody = Annotated[bytes, Depends(verify_webhook_signature)]
