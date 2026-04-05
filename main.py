import json

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.routers import auth, pull_requests, repositories, reviews, skills, stats
from app.webhook import dispatch_event, verify_webhook_signature

app = FastAPI(title="Almagest Reviewer")

# 인증 라우터 (보호 없음 — 로그인 자체는 인증 불필요)
app.include_router(auth.router, prefix="/api")

# 보호된 API 라우터
_auth_dep = [Depends(get_current_user)]
app.include_router(stats.router, prefix="/api", dependencies=_auth_dep)
app.include_router(repositories.router, prefix="/api", dependencies=_auth_dep)
app.include_router(pull_requests.router, prefix="/api", dependencies=_auth_dep)
app.include_router(reviews.router, prefix="/api", dependencies=_auth_dep)
app.include_router(skills.router, prefix="/api", dependencies=_auth_dep)


@app.get("/health")
async def health_check():
    """서비스 헬스체크 엔드포인트.

    Returns:
        서비스 상태와 이름을 담은 딕셔너리.
    """
    return {"status": "ok", "service": "almagest-reviewer"}


@app.post("/webhook")
async def github_webhook(request: Request, session: AsyncSession = Depends(get_db)):
    """GitHub App 웹훅 이벤트를 처리한다.

    Args:
        request: 웹훅 요청 (X-Hub-Signature-256 서명 포함).
        session: 비동기 DB 세션.

    Returns:
        처리 결과 JSON (``{"status": "success"}``).

    Raises:
        HTTPException: 웹훅 서명 검증 실패 시 403.
    """
    verified_body = await verify_webhook_signature(request)
    payload = json.loads(verified_body)

    event = request.headers.get("x-github-event", "unknown")
    action = payload.get("action", "none")
    logger.info(f"📩 이벤트 수신: event={event}, action={action}")

    await dispatch_event(event, action, payload, session)

    return JSONResponse({"status": "success"})


