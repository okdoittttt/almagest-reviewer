import json

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.github import GitHubClient, PRDataCollector
from app.reviewer import run_review
from app.services.review_service import persist_review_result
from app.webhook import verify_webhook_signature

app = FastAPI()
github_client = GitHubClient()
pr_collector = PRDataCollector(github_client)

@app.get("/")
async def health_check():
    """Health check endpoint"""
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
    if payload.get("action") in ["opened", "synchronize"]:
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
