import json

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from loguru import logger

from app.github import GitHubClient
from app.webhook import verify_webhook_signature

app = FastAPI()
github_client = GitHubClient()

@app.post("/github/webhook")
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
        
        # PR의 변경된 파일 목록 가져오기
        files = await github_client.get_pr_files(
            installation_id=installation_id,
            repo_owner=repo_owner,
            repo_name=repo_name,
            pull_number=pr_number
        )
        
        # 코멘트 작성
        comment = f"코드 리뷰를 시작합니다!\n\n변경된 파일: {len(files)}개"
        await github_client.create_pr_comment(
            installation_id=installation_id,
            repo_owner=repo_owner,
            repo_name=repo_name,
            pull_number=pr_number,
            comment_body=comment
        )
        
        logger.info(f"Processed PR #{pr_number} from {repo_owner}/{repo_name}")
    
    return JSONResponse({"status": "success"})