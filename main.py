import json

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from loguru import logger

from app.github import GitHubClient, PRDataCollector
from app.webhook import verify_webhook_signature
from app.reviewer import run_review

app = FastAPI()
github_client = GitHubClient()
pr_collector = PRDataCollector(github_client)

@app.get("/")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "almagest-reviewer"}

@app.post("/webhook")
async def github_webhook(request: Request):
    # Webhook 서명 검증
    verified_body = await verify_webhook_signature(request)

    # 검증된 body를 JSON으로 파싱
    payload = json.loads(verified_body)
    
    # PR 이벤트 처리
    if payload.get("action") in ["opened", "synchronize"]:
        installation_id = str(payload["installation"]["id"])
        repo = payload["repository"]
        pr = payload["pull_request"]

        # PR 정보 추출
        repo_owner = repo["owner"]["login"]
        repo_name = repo["name"]
        pr_number = pr["number"]

        # PR 데이터 수집 (파일, 커밋, 통계 등 모든 정보)
        pr_data = await pr_collector.collect_pr_data(
            installation_id=installation_id,
            repo_owner=repo_owner,
            repo_name=repo_name,
            pull_number=pr_number,
            include_commits=True  # 커밋 목록 포함
        )

        # LanGraph 기반 AI 코드 리뷰 실행
        logger.info(f"🤖 AI 코드 리뷰 시작: PR #{pr_number}")

        review_result = await run_review(
            pr_data=pr_data,
            installation_id=installation_id,
            repo_owner=repo_owner,
            repo_name=repo_name
        )

        # 최종 리뷰 코멘트 추출
        final_review = review_result.get("final_review", "리뷰 생성 실패")
        review_decision = review_result.get("review_decision", "COMMENT")

        # GitHub에 리뷰 코멘트 게시
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
