import json

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from loguru import logger

from app.github import GitHubClient, PRDataCollector
from app.webhook import verify_webhook_signature

app = FastAPI()
github_client = GitHubClient()
pr_collector = PRDataCollector(github_client)

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

        # PR 데이터 수집 (파일, 커밋, 통계 등 모든 정보)
        pr_data = await pr_collector.collect_pr_data(
            installation_id=installation_id,
            repo_owner=repo_owner,
            repo_name=repo_name,
            pull_number=pr_number,
            include_commits=True  # 커밋 목록 포함
        )

        # 수집된 데이터로 코멘트 작성
        comment = f"""🤖 코드 리뷰를 시작합니다!

**PR 정보**
- 제목: {pr_data.title}
- 작성자: @{pr_data.author.login}
- 브랜치: `{pr_data.head_branch}` → `{pr_data.base_branch}`

**변경 사항**
- 파일: {pr_data.changed_files_count}개
- 커밋: {pr_data.commits_count}개
- 추가: +{pr_data.total_additions} / 삭제: -{pr_data.total_deletions}

**변경된 파일 목록**
"""
        for file in pr_data.files[:10]:  # 최대 10개만 표시
            status_emoji = "✨" if file.is_new_file else "📝" if file.status == "modified" else "🗑️"
            comment += f"\n{status_emoji} `{file.filename}` (+{file.additions}/-{file.deletions})"

        if pr_data.changed_files_count > 10:
            comment += f"\n\n... 외 {pr_data.changed_files_count - 10}개 파일"

        await github_client.create_pr_comment(
            installation_id=installation_id,
            repo_owner=repo_owner,
            repo_name=repo_name,
            pull_number=pr_number,
            comment_body=comment
        )

        logger.info(
            f"Processed PR #{pr_number} from {repo_owner}/{repo_name}: "
            f"{pr_data.changed_files_count} files, {pr_data.commits_count} commits"
        )
    
    return JSONResponse({"status": "success"})