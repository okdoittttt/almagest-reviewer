import json
from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.github import github_client, pr_collector
from app.reviewer import run_review
from app.routers import auth, pull_requests, repositories, reviews, skills, stats
from app.services.review_service import persist_review_result, update_pr_state
from app.webhook import verify_webhook_signature

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
    return {"status": "ok", "service": "almagest-reviewer"}


@app.post("/webhook")
async def github_webhook(request: Request, session: AsyncSession = Depends(get_db)):
    # Webhook 서명 검증
    verified_body = await verify_webhook_signature(request)

    # 검증된 body를 JSON으로 파싱
    payload = json.loads(verified_body)

    event = request.headers.get("x-github-event", "unknown")
    action = payload.get("action", "none")
    logger.info(f"📩 이벤트 수신: event={event}, action={action}")

    # PR 이벤트 처리
    if action == "closed":
        repo = payload["repository"]
        pr = payload["pull_request"]

        github_repo_id = repo["id"]
        pr_number = pr["number"]
        new_state = "merged" if pr.get("merged") else "closed"

        logger.info(f"🔒 PR #{pr_number} 상태 업데이트: {new_state}")
        await update_pr_state(session, github_repo_id, pr_number, new_state)
        logger.info(f"✅ PR #{pr_number} 상태 업데이트 완료")

    elif action in ["opened", "synchronize"]:
        installation_id = str(payload["installation"]["id"])
        repo = payload["repository"]
        pr = payload["pull_request"]

        github_repo_id = repo["id"]
        github_pr_id = pr["id"]
        repo_owner = repo["owner"]["login"]
        repo_name = repo["name"]
        pr_number = pr["number"]

        logger.info(f"📋 PR 데이터 수집 시작: {repo_owner}/{repo_name} #{pr_number}")
        pr_data = await pr_collector.collect_pr_data(
            installation_id=installation_id,
            repo_owner=repo_owner,
            repo_name=repo_name,
            pull_number=pr_number,
            include_commits=True
        )
        logger.info(f"📋 PR 데이터 수집 완료: {pr_data.changed_files_count}개 파일, {pr_data.commits_count}개 커밋")

        logger.info(f"🤖 AI 코드 리뷰 시작: PR #{pr_number}")
        review_result = await run_review(
            pr_data=pr_data,
            installation_id=installation_id,
            repo_owner=repo_owner,
            repo_name=repo_name
        )
        logger.info(f"🤖 AI 코드 리뷰 완료: decision={review_result.get('review_decision')}, errors={review_result.get('errors')}")

        logger.info("💾 DB 저장 시작")
        await persist_review_result(
            session=session,
            installation_id=installation_id,
            github_repo_id=github_repo_id,
            github_pr_id=github_pr_id,
            pr_data=pr_data,
            review_result=review_result,
        )
        logger.info("💾 DB 저장 완료")

        final_review = review_result.get("final_review", "리뷰 생성 실패")
        review_decision = review_result.get("review_decision", "COMMENT")

        logger.info(f"💬 GitHub 코멘트 게시 시작: PR #{pr_number}")
        await github_client.create_pr_comment(
            installation_id=installation_id,
            repo_owner=repo_owner,
            repo_name=repo_name,
            pull_number=pr_number,
            comment_body=final_review
        )

        logger.info(
            f"✅ PR #{pr_number} 리뷰 완료: {review_decision} - "
            f"{pr_data.changed_files_count} files, {len(review_result.get('file_reviews', []))} reviews"
        )

    return JSONResponse({"status": "success"})


# SPA catch-all: /api/* 와 /webhook, /health 를 제외한 모든 경로를 index.html 로 서빙
@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    index = _FRONTEND_DIST / "index.html"
    if index.exists():
        return FileResponse(index)
    return JSONResponse({"status": "ok", "service": "almagest-reviewer"})
