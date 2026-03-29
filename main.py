import json
from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
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

# 프론트엔드 정적 파일 서빙
_FRONTEND_DIST = Path(__file__).parent / "frontend" / "dist"
if _FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=_FRONTEND_DIST / "assets"), name="assets")


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


# SPA catch-all: /api/* 와 /webhook, /health 를 제외한 모든 경로를 index.html 로 서빙
@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    """SPA catch-all 라우터. /api, /webhook, /health를 제외한 모든 경로에 index.html을 반환한다.

    Args:
        full_path: 요청 경로.

    Returns:
        프론트엔드 index.html 또는 서비스 상태 JSON (빌드 파일이 없는 경우).
    """
    index = _FRONTEND_DIST / "index.html"
    if index.exists():
        return FileResponse(index)
    return JSONResponse({"status": "ok", "service": "almagest-reviewer"})
